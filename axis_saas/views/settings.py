"""
AXIS views – settings module.
"""

import re
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse, Http404
from django.contrib import messages
from django.db.models import Sum, Q, Exists, OuterRef, Max
from django.db.models.functions import TruncMonth, TruncDay
from django.db.models import Count
from django.core.paginator import Paginator
from django.db import connection
from django_tenants.utils import schema_context
from decimal import Decimal
from datetime import date, timedelta, datetime
from collections import defaultdict
import json
import re
from functools import wraps
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from ..models import SchoolClient, Student, FeeStructure, FeeRecord, PaymentTransaction, SchoolFeeSettings, Product, ProductCategory, WingCategory
from ..forms import StudentForm, FeeCollectionForm, FeeSettingsForm, FeeStructureForm, FamilyPaymentForm
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.db import IntegrityError
from ..models import ManualGenerationLog

from .helpers import *

@require_tenant_type(['school'])
def settings(request, schema_name):
    tenant = get_tenant(request, schema_name)
    if request.method == 'POST':
        if tenant.tenant_type == 'wing_school' and request.POST.get('category_action'):
            main_name = request.POST.get('main_category', '').strip()
            sub_name = request.POST.get('sub_category', '').strip()
            category_id = request.POST.get('category_id')
            with schema_context(schema_name):
                is_add_to_existing_campus = (
                    request.POST.get('category_action') == 'add'
                    and request.POST.get('main_category_id')
                )
                action = request.POST.get('category_action')
                is_main_delete = action == 'delete_main' and category_id
                if not main_name and not is_add_to_existing_campus and not is_main_delete:
                    messages.error(request, 'Main category is required.')
                else:
                    try:
                        category_action = request.POST.get('category_action')
                        if category_action == 'manage':
                            with transaction.atomic():
                                main_category = get_object_or_404(
                                    WingCategory.objects.select_for_update(),
                                    pk=request.POST.get('main_category_id'),
                                    parent__isnull=True,
                                    is_active=True,
                                )
                                main_category.name = main_name
                                main_category.save(update_fields=['name'])
                                deleted_ids = {
                                    value for value in request.POST.getlist('deleted_subcategories')
                                    if value.isdecimal()
                                }
                                child_ids = request.POST.getlist('subcategory_ids')
                                child_names = request.POST.getlist('subcategory_names')
                                if len(child_ids) != len(child_names):
                                    raise ValueError('Campus wing data was incomplete. Please try again.')
                                for child_id, child_name in zip(child_ids, child_names):
                                    child_name = child_name.strip()
                                    if not child_id:
                                        if not child_name:
                                            raise ValueError('Wing names cannot be empty.')
                                        child, _ = WingCategory.objects.get_or_create(
                                            parent=main_category,
                                            name=child_name,
                                            defaults={'is_active': True},
                                        )
                                        if not child.is_active:
                                            child.is_active = True
                                            child.save(update_fields=['is_active'])
                                        continue
                                    if not child_id.isdecimal():
                                        raise ValueError('An invalid wing was submitted.')
                                    child = get_object_or_404(
                                        WingCategory.objects.select_for_update(),
                                        pk=int(child_id),
                                        parent=main_category,
                                        is_active=True,
                                    )
                                    if child_id in deleted_ids:
                                        child.is_active = False
                                        child.save(update_fields=['is_active'])
                                        continue
                                    if not child_name:
                                        raise ValueError('Wing names cannot be empty.')
                                    child.name = child_name
                                    child.save(update_fields=['name'])
                            messages.success(request, 'Campus and wing changes saved.')
                        elif category_action == 'delete_main' and category_id:
                            with transaction.atomic():
                                main_category = get_object_or_404(
                                    WingCategory.objects.select_for_update(),
                                    pk=category_id,
                                    parent__isnull=True,
                                    is_active=True,
                                )
                                WingCategory.objects.filter(
                                    parent=main_category,
                                    is_active=True,
                                ).update(is_active=False)
                                main_category.is_active = False
                                main_category.save(update_fields=['is_active'])
                            messages.success(request, 'Campus and its wings were deactivated.')
                        elif category_action == 'edit' and category_id:
                            category = get_object_or_404(WingCategory, pk=category_id, is_active=True)
                            main_category = category.parent or category
                            main_category.name = main_name
                            main_category.save(update_fields=['name'])
                            if sub_name:
                                if category.parent:
                                    category.name = sub_name
                                    category.save(update_fields=['name'])
                                else:
                                    WingCategory.objects.create(name=sub_name, parent=main_category)
                            elif category.parent:
                                category.is_active = False
                                category.save(update_fields=['is_active'])
                            messages.success(request, 'Campus / wing category updated successfully.')
                        elif category_action == 'add':
                            main_category_id = request.POST.get('main_category_id', '').strip()
                            if main_category_id:
                                if not main_category_id.isdecimal():
                                    raise ValueError('Select a valid campus.')
                                main_category = get_object_or_404(
                                    WingCategory,
                                    pk=int(main_category_id),
                                    parent__isnull=True,
                                    is_active=True,
                                )
                            else:
                                main_category, _ = WingCategory.objects.get_or_create(
                                    name=main_name,
                                    parent=None,
                                    defaults={'is_active': True},
                                )
                            if not main_category.is_active:
                                main_category.is_active = True
                                main_category.save(update_fields=['is_active'])
                            if sub_name:
                                WingCategory.objects.update_or_create(
                                    name=sub_name,
                                    parent=main_category,
                                    defaults={'is_active': True},
                                )
                            messages.success(request, 'Campus / wing category added successfully.')
                    except ValueError as error:
                        messages.error(request, str(error))
                    except IntegrityError:
                        messages.error(request, 'A category with this name already exists under the selected main category.')
            if request.POST.get('return_to') == 'classes_management':
                classes_url = reverse('classes_management', kwargs={'schema_name': schema_name})
                return redirect(f'{classes_url}?open_campus_management=1')
            return redirect('settings', schema_name=schema_name)
        school_name = request.POST.get('school_name', '').strip()
        if school_name:
            tenant.name = school_name
        admin_username = request.POST.get('admin_username', '').strip()
        admin_password = request.POST.get('admin_password', '')
        admin_password_confirm = request.POST.get('admin_password_confirm', '')
        if admin_username:
            tenant.admin_username = admin_username
        if admin_password:
            if admin_password == admin_password_confirm:
                tenant._raw_password = admin_password
                tenant.set_password(admin_password)
            else:
                messages.error(request, 'Passwords do not match.')
                return redirect('settings', schema_name=schema_name)
        if request.FILES.get('school_logo'):
            tenant.school_logo = request.FILES['school_logo']
        tenant.save()
        messages.success(request, 'Settings updated successfully.')
        return redirect('settings', schema_name=schema_name)
    context = {'tenant': tenant, 'logo_url': tenant.school_logo.url if tenant.school_logo else None}
    template = 'tenant/wing_school_settings.html' if tenant.tenant_type == 'wing_school' else 'tenant/settings.html'
    with schema_context(schema_name):
        context['wing_categories'] = WingCategory.objects.filter(is_active=True).select_related('parent') if tenant.tenant_type == 'wing_school' else []
        context['wing_parents'] = WingCategory.objects.filter(is_active=True, parent__isnull=True) if tenant.tenant_type == 'wing_school' else []
    return render(request, template, context)

def mobile_settings(request, schema_name):
    tenant = get_tenant(request, schema_name)
    if request.method == 'POST':
        school_name = request.POST.get('school_name', '').strip()
        if school_name:
            tenant.name = school_name
        admin_username = request.POST.get('admin_username', '').strip()
        admin_password = request.POST.get('admin_password', '')
        admin_password_confirm = request.POST.get('admin_password_confirm', '')
        if admin_username:
            tenant.admin_username = admin_username
        if admin_password:
            if admin_password == admin_password_confirm:
                tenant._raw_password = admin_password
                tenant.set_password(admin_password)
            else:
                messages.error(request, 'Passwords do not match.')
                return redirect('settings', schema_name=schema_name)
        if request.FILES.get('school_logo'):
            tenant.school_logo = request.FILES['school_logo']
        tenant.save()
        messages.success(request, 'Settings updated successfully.')
        return redirect('settings', schema_name=schema_name)
    context = {'tenant': tenant, 'logo_url': tenant.school_logo.url if tenant.school_logo else None}
    template = 'mobile/wing_school_settings.html' if tenant.tenant_type == 'wing_school' else 'mobile/settings.html'
    if tenant.tenant_type == 'wing_school':
        with schema_context(schema_name):
            context['wing_categories'] = WingCategory.objects.filter(is_active=True).select_related('parent')
            context['wing_parents'] = WingCategory.objects.filter(is_active=True, parent__isnull=True)
    return render(request, template, context)
