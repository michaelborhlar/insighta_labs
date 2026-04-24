from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Profile
from .serializers import ProfileSerializer
from .parser import parse_natural_language_query

VALID_SORT_FIELDS = {'age', 'created_at', 'gender_probability'}
VALID_ORDERS = {'asc', 'desc'}
VALID_GENDERS = {'male', 'female'}
VALID_AGE_GROUPS = {'child', 'teenager', 'adult', 'senior'}
MAX_LIMIT = 50
DEFAULT_LIMIT = 10
DEFAULT_PAGE = 1


def error_response(message, http_status=status.HTTP_400_BAD_REQUEST):
    return Response({'status': 'error', 'message': message}, status=http_status)


def apply_filters(queryset, params):
    """
    Apply all supported filters to a queryset.
    Returns (filtered_queryset, error_response_or_None).
    """
    # gender
    gender = params.get('gender')
    if gender is not None:
        if gender not in VALID_GENDERS:
            return None, error_response('Invalid query parameters', status.HTTP_422_UNPROCESSABLE_ENTITY)
        queryset = queryset.filter(gender=gender)

    # age_group
    age_group = params.get('age_group')
    if age_group is not None:
        if age_group not in VALID_AGE_GROUPS:
            return None, error_response('Invalid query parameters', status.HTTP_422_UNPROCESSABLE_ENTITY)
        queryset = queryset.filter(age_group=age_group)

    # country_id
    country_id = params.get('country_id')
    if country_id is not None:
        queryset = queryset.filter(country_id=country_id.upper())

    # min_age / max_age
    min_age = params.get('min_age')
    if min_age is not None:
        try:
            queryset = queryset.filter(age__gte=int(min_age))
        except (ValueError, TypeError):
            return None, error_response('Invalid query parameters', status.HTTP_422_UNPROCESSABLE_ENTITY)

    max_age = params.get('max_age')
    if max_age is not None:
        try:
            queryset = queryset.filter(age__lte=int(max_age))
        except (ValueError, TypeError):
            return None, error_response('Invalid query parameters', status.HTTP_422_UNPROCESSABLE_ENTITY)

    # min_gender_probability
    min_gender_prob = params.get('min_gender_probability')
    if min_gender_prob is not None:
        try:
            queryset = queryset.filter(gender_probability__gte=float(min_gender_prob))
        except (ValueError, TypeError):
            return None, error_response('Invalid query parameters', status.HTTP_422_UNPROCESSABLE_ENTITY)

    # min_country_probability
    min_country_prob = params.get('min_country_probability')
    if min_country_prob is not None:
        try:
            queryset = queryset.filter(country_probability__gte=float(min_country_prob))
        except (ValueError, TypeError):
            return None, error_response('Invalid query parameters', status.HTTP_422_UNPROCESSABLE_ENTITY)

    return queryset, None


def apply_sorting(queryset, params):
    """Apply sort_by and order params. Returns (sorted_qs, error_or_None)."""
    sort_by = params.get('sort_by')
    order = params.get('order', 'asc')

    if sort_by is not None and sort_by not in VALID_SORT_FIELDS:
        return None, error_response('Invalid query parameters', status.HTTP_422_UNPROCESSABLE_ENTITY)

    if order not in VALID_ORDERS:
        return None, error_response('Invalid query parameters', status.HTTP_422_UNPROCESSABLE_ENTITY)

    if sort_by:
        field = f'-{sort_by}' if order == 'desc' else sort_by
        queryset = queryset.order_by(field)
    else:
        queryset = queryset.order_by('created_at')

    return queryset, None


def apply_pagination(queryset, params):
    """
    Apply page/limit pagination.
    Returns (page_int, limit_int, paginated_qs, error_or_None).
    """
    try:
        page = int(params.get('page', DEFAULT_PAGE))
        if page < 1:
            raise ValueError
    except (ValueError, TypeError):
        return None, None, None, error_response('Invalid query parameters', status.HTTP_422_UNPROCESSABLE_ENTITY)

    try:
        limit = int(params.get('limit', DEFAULT_LIMIT))
        if limit < 1:
            raise ValueError
        limit = min(limit, MAX_LIMIT)
    except (ValueError, TypeError):
        return None, None, None, error_response('Invalid query parameters', status.HTTP_422_UNPROCESSABLE_ENTITY)

    offset = (page - 1) * limit
    return page, limit, queryset[offset:offset + limit], None


class ProfileListView(APIView):
    """GET /api/profiles — filtering, sorting, pagination."""

    def get(self, request):
        params = request.query_params

        queryset = Profile.objects.all()

        # Filtering
        queryset, err = apply_filters(queryset, params)
        if err:
            return err

        # Sorting
        queryset, err = apply_sorting(queryset, params)
        if err:
            return err

        total = queryset.count()

        # Pagination
        page, limit, paginated_qs, err = apply_pagination(queryset, params)
        if err:
            return err

        serializer = ProfileSerializer(paginated_qs, many=True)
        return Response({
            'status': 'success',
            'page': page,
            'limit': limit,
            'total': total,
            'data': serializer.data,
        })


class ProfileSearchView(APIView):
    """GET /api/profiles/search?q=<natural language query>"""

    def get(self, request):
        q = request.query_params.get('q', '').strip()

        if not q:
            return error_response('Missing or empty parameter', status.HTTP_400_BAD_REQUEST)

        parsed = parse_natural_language_query(q)
        if parsed is None:
            return Response(
                {'status': 'error', 'message': 'Unable to interpret query'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = Profile.objects.all()

        # Apply parsed filters
        queryset, err = apply_filters(queryset, parsed)
        if err:
            return err

        # Default sort by age for search results
        queryset = queryset.order_by('age')

        total = queryset.count()

        # Pagination from query params
        page, limit, paginated_qs, err = apply_pagination(queryset, request.query_params)
        if err:
            return err

        serializer = ProfileSerializer(paginated_qs, many=True)
        return Response({
            'status': 'success',
            'page': page,
            'limit': limit,
            'total': total,
            'data': serializer.data,
        })
