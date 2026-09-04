import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django

django.setup()

from fastapi import Depends, FastAPI, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from rest_framework_simplejwt.tokens import AccessToken
from starlette.middleware.wsgi import WSGIMiddleware
from config.api_wsgi import application as django_api_wsgi_application

app = FastAPI(
    title='Pharmacy Management System API',
    version='1.0.0',
    docs_url=None,
    openapi_url=None,
)
bearer_scheme = HTTPBearer(auto_error=False)

MODULE_ENDPOINTS = {
    'Accounts': 'users',
    'Inventory': 'categories medicines batches',
    'Suppliers & Procurement': 'suppliers purchase-orders purchase-order-items',
    'Sales & POS': 'sales sale-items',
    'Prescriptions': 'prescriptions prescription-items',
    'Analytics': 'stock-audits dashboard',
}


def require_token(credentials: HTTPAuthorizationCredentials = None):
    if credentials is None:
        raise HTTPException(status_code=401, detail='Authentication credentials were not provided.')
    try:
        return AccessToken(credentials.credentials)
    except Exception as error:
        raise HTTPException(status_code=401, detail='Invalid or expired token.') from error


@app.get('/health', tags=['system'])
def health_check():
    return {'status': 'online', 'service': 'pharmacy-management-system'}


@app.get('/api/fast/medicines/barcode/{barcode}', tags=['fastapi'])
def medicine_by_barcode(barcode: str, credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    require_token(credentials)
    from inventory.models import Medicine

    try:
        medicine = Medicine.objects.select_related('category').get(barcode=barcode)
    except Medicine.DoesNotExist as error:
        raise HTTPException(status_code=404, detail='Medicine not found.') from error
    return {
        'id': str(medicine.id), 'name': medicine.name, 'generic_name': medicine.generic_name,
        'barcode': medicine.barcode, 'category': medicine.category.name,
        'prescription_required': medicine.is_prescription_required,
    }


@app.get('/api/openapi.json', include_in_schema=False)
def openapi_schema():
    from drf_spectacular.generators import SchemaGenerator

    schema = SchemaGenerator().get_schema(request=None, public=True)
    schema['servers'] = [{'url': '/api'}]
    return JSONResponse(schema)


@app.get('/api/docs', include_in_schema=False)
def swagger_ui():
    return get_swagger_ui_html(
        openapi_url='/api/openapi.json',
        title=f'{app.title} - Swagger UI',
    )


app.mount('/api', WSGIMiddleware(django_api_wsgi_application))