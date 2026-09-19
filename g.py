#!/usr/bin/env python3
"""
axis_patcher.py - STAFF_LIST_UX_OVERHAUL_V1

Fixes:
  1. Intermittent empty staff / student list on first render.
     Root cause: Paginator.get_page() returns a Page whose
     object_list is a lazy queryset. The template iterates that
     queryset AFTER `with schema_context(...)` exits, by which
     time the connection's search_path can revert to 'public',
     producing zero rows.
     Fix: materialize them inside the schema_context block.

  2. Fixture modal always says "No absent periods today".
     Root cause: the orphan-period filter dropped every PTA row
     whose (day, period) was not present in the class's
     PeriodsTimetable.days JSON, which is stale for classes set
     up before the timetable feature.
     Fix: show every PTA row for a teacher on leave today.

  3. Rebuilds the three staff-list modals (Assign Subjects,
     Manage Class Teachers, Assign Fixture) with form-on-top,
     confirm dialogs, replace flow, subject-teacher-only
     candidates, and wing/single class display via the
     tenant-aware helper.

  4. Backend endpoints return class_display + richer data.
"""
import argparse
import ast
import logging
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

LOG = logging.getLogger('axis_patcher')


def _ts():
    return datetime.now().strftime('%H:%M:%S')


def info(msg, *args):
    LOG.info('[%s] ' + msg, _ts(), *args)


def warn(msg, *args):
    LOG.warning('[%s] ' + msg, _ts(), *args)


def err(msg, *args):
    LOG.error('[%s] ' + msg, _ts(), *args)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read(path):
    if not path.exists():
        return None
    return path.read_text(encoding='utf-8')


def _write(path, content, dry):
    if str(path).endswith('.py'):
        try:
            ast.parse(content)
        except SyntaxError as exc:
            err('SYNTAX ERROR in %s: %s', path, exc)
            return False
    if dry:
        info('[DRY] would write %s (%d bytes)', path, len(content))
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding='utf-8')
    info('wrote %s (%d bytes)', path, len(content))
    return True


def _replace_between(text, start_anchor, end_anchor, new_block):
    s = text.find(start_anchor)
    if s < 0:
        return None, 'start anchor missing'
    e = text.find(end_anchor, s)
    if e < 0:
        return None, 'end anchor missing'
    e_end = e + len(end_anchor)
    return text[:s] + new_block + text[e_end:], None


def _run_command(root, args, dry):
    cmd_disp = ' '.join(str(a) for a in args)
    if dry:
        info('[DRY] %s', cmd_disp)
        return
    info('$ %s', cmd_disp)
    try:
        res = subprocess.run(
            args, cwd=str(root), capture_output=True, text=True, timeout=300,
        )
        if res.stdout:
            for line in res.stdout.strip().splitlines():
                info('  %s', line)
        if res.stderr:
            for line in res.stderr.strip().splitlines():
                warn('  %s', line)
        if res.returncode != 0:
            warn('command exited %d (continuing)', res.returncode)
    except Exception as exc:
        warn('command failed: %s', exc)


# ===========================================================================
# 1. helpers.py — materialize lazy querysets inside schema_context
# ===========================================================================

def patch_helpers(root, dry):
    path = root / 'axis_saas' / 'views' / 'helpers.py'
    text = _read(path)
    if text is None:
        warn('helpers.py not found')
        return

    changed = False

    staff_anchor = (
        '        paginator = Paginator(staff_qs, 50)\n'
        '        page_obj = paginator.get_page(page_number)\n'
    )
    if staff_anchor in text and 'STAFF_LIST_LAZY_FIX_V1' not in text:
        text = text.replace(
            staff_anchor,
            staff_anchor +
            '        # STAFF_LIST_LAZY_FIX_V1: force evaluation of the\n'
            '        # page\'s object_list INSIDE the schema_context.\n'
            '        page_obj.object_list = list(page_obj.object_list)\n',
            1,
        )
        changed = True

    staff_cls_anchor = (
        '        classes = SchoolClass.objects.filter(\n'
        '            is_active=True,\n'
        '        ).order_by(\'name\', \'section\')\n'
        '        sections = classes.values_list(\n'
        '            \'section\', flat=True,\n'
        '        ).distinct().order_by(\'section\')\n'
    )
    if staff_cls_anchor in text:
        text = text.replace(
            staff_cls_anchor,
            '        classes_qs = SchoolClass.objects.filter(\n'
            '            is_active=True,\n'
            '        ).order_by(\'name\', \'section\')\n'
            '        # STAFF_LIST_LAZY_FIX_V1\n'
            '        sections = list(classes_qs.values_list(\n'
            '            \'section\', flat=True,\n'
            '        ).distinct().order_by(\'section\'))\n'
            '        classes = list(classes_qs)\n',
            1,
        )
        changed = True

    student_anchor = (
        '        paginator = Paginator(students, 20)\n'
        '        page_obj = paginator.get_page(page_number)\n'
    )
    if student_anchor in text and 'STUDENT_LIST_LAZY_FIX_V1' not in text:
        text = text.replace(
            student_anchor,
            student_anchor +
            '        # STUDENT_LIST_LAZY_FIX_V1\n'
            '        page_obj.object_list = list(page_obj.object_list)\n',
            1,
        )
        changed = True

    student_cls_anchor = (
        '        classes = SchoolClass.objects.filter(is_active=True).select_related(\'wing_category\').order_by(\'name\', \'section\')\n'
    )
    if student_cls_anchor in text:
        text = text.replace(
            student_cls_anchor,
            '        # STUDENT_LIST_LAZY_FIX_V1\n'
            '        classes = list(\n'
            '            SchoolClass.objects.filter(is_active=True)\n'
            '            .select_related(\'wing_category\')\n'
            '            .order_by(\'name\', \'section\')\n'
            '        )\n',
            1,
        )
        changed = True

    cat_anchor = (
        '        categories = WingCategory.objects.filter(\n'
        '            is_active=True,\n'
        '            parent__isnull=False,\n'
        '        ).select_related(\'parent\').order_by(\'parent__name\', \'name\') if tenant.tenant_type == \'wing_school\' else []\n'
    )
    if cat_anchor in text:
        text = text.replace(
            cat_anchor,
            '        categories = list(WingCategory.objects.filter(\n'
            '            is_active=True,\n'
            '            parent__isnull=False,\n'
            '        ).select_related(\'parent\').order_by(\'parent__name\', \'name\')) if tenant.tenant_type == \'wing_school\' else []\n',
            1,
        )
        changed = True

    if changed:
        _write(path, text, dry)
    else:
        info('helpers.py: nothing to do (idempotent)')


# ===========================================================================
# 2. assign_teachers.py — stop hiding genuine absent periods
# ===========================================================================

def patch_assign_teachers(root, dry):
    path = root / 'axis_saas' / 'views' / 'assign_teachers.py'
    text = _read(path)
    if text is None:
        warn('assign_teachers.py not found')
        return

    if 'FIXTURE_FALSE_EMPTY_FIX_V2' in text:
        info('assign_teachers.py: already patched')
        return

    old_block = (
        '        # FIXTURE_FALSE_EMPTY_FIX_V1: a class without a current\n'
        '        # ClassTimetableAssignment previously made every one of its\n'
        '        # PeriodTeacherAssignment rows look like an orphan, so a\n'
        '        # teacher who was genuinely on leave and had a period today\n'
        '        # was silently dropped and the modal showed the useless\n'
        '        # \'No absent periods today\' message. We now only filter a\n'
        '        # period out when we have a valid timetable for the class\n'
        '        # AND that (day, period) pair is not in it.\n'
        '        def _keep_absent_period(ap):\n'
        '            valid = _valid_by_class.get(ap.school_class_id)\n'
        '            if valid is None:\n'
        '                return True\n'
        '            return (ap.day_of_week, ap.period_order) in valid\n'
        '        absent_periods = [ap for ap in absent_periods\n'
        '                          if _keep_absent_period(ap)]\n'
    )
    new_block = (
        '        # FIXTURE_FALSE_EMPTY_FIX_V2: keep every PTA row for a\n'
        '        # teacher on leave today. The V1 orphan filter dropped\n'
        '        # rows whenever the class timetable JSON was out of\n'
        '        # sync with the PTA rows, hiding teachers who\n'
        '        # genuinely had a period today.\n'
        '        absent_periods = list(absent_periods)\n'
    )

    if old_block in text:
        text = text.replace(old_block, new_block, 1)
        _write(path, text, dry)
        return

    pattern = re.compile(
        r'        def _keep_absent_period\(ap\):\n'
        r'            valid = _valid_by_class\.get\(ap\.school_class_id\)\n'
        r'            if valid is None:\n'
        r'                return True\n'
        r'            return \(ap\.day_of_week, ap\.period_order\) in valid\n'
        r'        absent_periods = \[ap for ap in absent_periods\n'
        r'                          if _keep_absent_period\(ap\)\]\n',
    )
    new_text, n = pattern.subn(new_block, text)
    if n == 0:
        warn('assign_teachers.py: filter block not found — '
             'skipping (may have been fixed differently)')
        return
    _write(path, new_text, dry)


# ===========================================================================
# 3. staff_extras.py — richer responses + display names
# ===========================================================================

def patch_staff_extras(root, dry):
    path = root / 'axis_saas' / 'views' / 'staff_extras.py'
    text = _read(path)
    if text is None:
        warn('staff_extras.py not found')
        return

    changed = False

    if 'from axis_saas.utils.class_display import get_class_display_name' not in text:
        import_anchor = 'from .helpers import (\n'
        if import_anchor in text:
            text = text.replace(
                import_anchor,
                'from axis_saas.utils.class_display import get_class_display_name\n'
                'from .helpers import (\n',
                1,
            )
            changed = True

    old_rows = (
        "        rows = [{\n"
        "            'id': a.id,\n"
        "            'class_id': a.school_class_id,\n"
        "            'class_name': str(a.school_class),\n"
    )
    new_rows = (
        "        tenant = get_tenant(request, schema_name)\n"
        "        def _cls_label(c):\n"
        "            try:\n"
        "                return get_class_display_name(c, tenant.tenant_type)\n"
        "            except Exception:\n"
        "                return str(c)\n"
        "        rows = [{\n"
        "            'id': a.id,\n"
        "            'class_id': a.school_class_id,\n"
        "            'class_name': _cls_label(a.school_class),\n"
    )
    if old_rows in text:
        text = text.replace(old_rows, new_rows, 1)
        changed = True

    old_ct_rows = (
        "        rows = [{\n"
        "            'id': c.id,\n"
        "            'name': str(c),\n"
        "            'section': c.section or '',\n"
    )
    new_ct_rows = (
        "        tenant = get_tenant(request, schema_name)\n"
        "        def _cls_label(c):\n"
        "            try:\n"
        "                return get_class_display_name(c, tenant.tenant_type)\n"
        "            except Exception:\n"
        "                return str(c)\n"
        "        rows = [{\n"
        "            'id': c.id,\n"
        "            'name': _cls_label(c),\n"
        "            'section': c.section or '',\n"
    )
    if old_ct_rows in text:
        text = text.replace(old_ct_rows, new_ct_rows, 1)
        changed = True

    old_resp = (
        "        return JsonResponse({\n"
        "            'ok': True,\n"
        "            'class_id': school_class.id,\n"
        "            'class_teacher_id': school_class.class_teacher_id,\n"
        "            'class_teacher_name': (\n"
        "                school_class.class_teacher.full_name\n"
        "                if school_class.class_teacher_id else ''\n"
        "            ),\n"
        "        })\n"
    )
    new_resp = (
        "        subjects = ''\n"
        "        if school_class.class_teacher_id:\n"
        "            subs = ClassSubject.objects.filter(\n"
        "                teacher_id=school_class.class_teacher_id, is_active=True,\n"
        "            ).values_list('subject__name', flat=True)\n"
        "            subjects = ', '.join(sorted(s for s in subs if s))\n"
        "        return JsonResponse({\n"
        "            'ok': True,\n"
        "            'class_id': school_class.id,\n"
        "            'class_teacher_id': school_class.class_teacher_id,\n"
        "            'class_teacher_name': (\n"
        "                school_class.class_teacher.full_name\n"
        "                if school_class.class_teacher_id else ''\n"
        "            ),\n"
        "            'class_teacher_subjects': subjects,\n"
        "        })\n"
    )
    if old_resp in text:
        text = text.replace(old_resp, new_resp, 1)
        changed = True

    if changed:
        _write(path, text, dry)
    else:
        info('staff_extras.py: nothing to do (idempotent)')


# ===========================================================================
# 4. staff_list.html — rebuild modals + JS
# ===========================================================================

NEW_MODALS = r"""<!-- STAFF_LIST_UX_OVERHAUL_V1 -->

<!-- ================= Modal: Assign Subjects ================= -->
<div class="slx slx-modal-backdrop" id="slxSubjectsModal">
    <div class="slx-modal slx-modal--lg">
        <div class="slx-modal-head">
            <div>
                <h3>Assign Subject Teachers</h3>
                <p>Pick a class, subject and teacher. Changing an existing teacher replaces them in that subject.</p>
            </div>
            <button type="button" class="slx-modal-close" data-close="slxSubjectsModal">&times;</button>
        </div>
        <div class="slx-modal-body">

            <div id="slxAsgFormCard" style="border:1px solid var(--slx-border); border-radius:12px; padding:1rem 1.1rem; background:var(--slx-surface-2); margin-bottom:1.25rem; transition:box-shadow .25s, background .25s;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:.75rem; gap:.5rem;">
                    <h4 id="slxAsgFormTitle" style="margin:0; font-size:.95rem; font-weight:800;">Add New Assignment</h4>
                    <button type="button" id="slxAsgResetBtn" class="slx-btn slx-btn-ghost" style="display:none;">Cancel Edit</button>
                </div>
                <div class="slx-form-grid">
                    <div class="slx-field">
                        <label for="slxAsgClass">Class</label>
                        <select id="slxAsgClass" class="slx-select"></select>
                    </div>
                    <div class="slx-field">
                        <label for="slxAsgSubject">Subject</label>
                        <select id="slxAsgSubject" class="slx-select"></select>
                    </div>
                    <div class="slx-field">
                        <label for="slxAsgTeacher">Teacher</label>
                        <select id="slxAsgTeacher" class="slx-select"></select>
                    </div>
                    <button type="button" class="slx-btn-filter" id="slxAsgSave" style="height:42px;">
                        Save
                    </button>
                </div>
                <div id="slxAsgCurrentInfo" style="display:none; margin-top:.75rem; padding:.65rem .85rem; border-radius:10px; background:rgba(245,158,11,.10); border:1px solid rgba(245,158,11,.3); font-size:.82rem; color:#92400e; line-height:1.45;">
                    <strong>Existing teacher:</strong>
                    <span id="slxAsgCurrentTeacher"></span>
                    <button type="button" id="slxAsgReplaceBtn" class="slx-btn slx-btn-danger" style="margin-left:.5rem; padding:.3rem .8rem; font-size:.75rem;">Replace with selection above</button>
                </div>
            </div>

            <hr class="slx-divider">

            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:.75rem; gap:.75rem; flex-wrap:wrap;">
                <h4 class="slx-section-title" style="margin:0;">Current Assignments</h4>
                <input type="text" id="slxAsgSearch" class="slx-input"
                       placeholder="Filter by class, subject or teacher…"
                       style="max-width:300px;">
            </div>
            <div id="slxAsgLoading" class="slx-loading">
                <div class="slx-skel" style="width:60%;"></div>
                <div class="slx-skel" style="width:85%;"></div>
                <div class="slx-skel" style="width:70%;"></div>
            </div>
            <div id="slxAsgWrapper" style="display:none; overflow-x:auto;">
                <table class="slx-mini-table" id="slxAsgTable">
                    <thead>
                        <tr>
                            <th>Class</th>
                            <th>Subject</th>
                            <th>Teacher</th>
                            <th style="width:180px; text-align:right;">Action</th>
                        </tr>
                    </thead>
                    <tbody id="slxAsgTbody"></tbody>
                </table>
            </div>
        </div>
        <div class="slx-modal-foot">
            <button type="button" class="slx-btn slx-btn-ghost" data-close="slxSubjectsModal">Close</button>
        </div>
    </div>
</div>

<!-- ================= Modal: Manage Class Teachers ================= -->
<div class="slx slx-modal-backdrop" id="slxClassTeachersModal">
    <div class="slx-modal slx-modal--lg">
        <div class="slx-modal-head">
            <div>
                <h3>Manage Class Teachers</h3>
                <p>Only subject teachers can lead a class. Assigning a teacher here removes them from any other class they currently lead.</p>
            </div>
            <button type="button" class="slx-modal-close" data-close="slxClassTeachersModal">&times;</button>
        </div>
        <div class="slx-modal-body">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:.85rem; gap:.75rem; flex-wrap:wrap;">
                <input type="text" id="slxCtSearch" class="slx-input"
                       placeholder="Filter by class or teacher…"
                       style="max-width:300px;">
                <span style="font-size:.78rem; color:var(--slx-muted);">Candidates: <strong id="slxCtCount">0</strong></span>
            </div>
            <div id="slxCtLoading" class="slx-loading">
                <div class="slx-skel" style="width:60%;"></div>
                <div class="slx-skel" style="width:85%;"></div>
                <div class="slx-skel" style="width:70%;"></div>
            </div>
            <div id="slxCtWrapper" style="display:none; overflow-x:auto;">
                <table class="slx-mini-table">
                    <thead>
                        <tr>
                            <th>Class</th>
                            <th style="width:70px;">Students</th>
                            <th>Current Class Teacher</th>
                            <th style="width:360px;">Assign / Change</th>
                        </tr>
                    </thead>
                    <tbody id="slxCtTbody"></tbody>
                </table>
            </div>
            <div id="slxCtEmpty" class="slx-modal-empty" style="display:none;">
                No class currently has a subject teacher available to lead it.
                Assign subject teachers first, then come back here.
            </div>
        </div>
        <div class="slx-modal-foot">
            <button type="button" class="slx-btn slx-btn-ghost" data-close="slxClassTeachersModal">Close</button>
        </div>
    </div>
</div>

<!-- ================= Modal: Today's Leave & Fixtures ================= -->
<div class="slx slx-modal-backdrop" id="slxFixturesModal">
    <div class="slx-modal slx-modal--lg">
        <div class="slx-modal-head">
            <div>
                <h3>Today's Leave &amp; Fixtures</h3>
                <p id="slxFixMeta">Loading…</p>
            </div>
            <button type="button" class="slx-modal-close" data-close="slxFixturesModal">&times;</button>
        </div>
        <div class="slx-modal-body">
            <div id="slxFixLoading" class="slx-loading">
                <div class="slx-skel" style="width:60%;"></div>
                <div class="slx-skel" style="width:85%;"></div>
                <div class="slx-skel" style="width:70%;"></div>
            </div>
            <div id="slxFixWrapper" style="display:none;"></div>
        </div>
        <div class="slx-modal-foot">
            <button type="button" class="slx-btn slx-btn-ghost" data-close="slxFixturesModal">Close</button>
        </div>
    </div>
</div>

<div class="slx-toast" id="slxToast"></div>
"""


NEW_SCRIPT = r"""{% block extra_scripts %}
<script>
(function () {
    'use strict';

    var SCHEMA = '{{ tenant.schema_name|escapejs }}';
    var URLS = {
        asgList:     '/portal/' + SCHEMA + '/api/staff/subject-assignments/',
        asgSave:     '/portal/' + SCHEMA + '/api/staff/assign-subject-teacher/',
        asgUnassign: '/portal/' + SCHEMA + '/api/staff/unassign-subject-teacher/',
        ctList:      '/portal/' + SCHEMA + '/api/staff/class-teacher-management/',
        ctSave:      '/portal/' + SCHEMA + '/api/staff/assign-class-teacher/',
        fixtures:    '/portal/' + SCHEMA + '/api/timetable/todays-leave/',
        subCreate:   '/portal/' + SCHEMA + '/api/timetable/substitute/create/',
        subDelete:   '/portal/' + SCHEMA + '/api/timetable/substitute/delete/'
    };

    function csrf() {
        var m = document.querySelector('meta[name="csrf-token"]');
        if (m && m.getAttribute('content')) return m.getAttribute('content');
        var parts = (document.cookie || '').split(';');
        for (var i = 0; i < parts.length; i++) {
            var c = parts[i].trim();
            if (c.indexOf('csrftoken=') === 0) return c.substring(10);
        }
        return '';
    }

    function toast(msg, kind) {
        var el = document.getElementById('slxToast');
        if (!el) return;
        el.textContent = msg;
        el.className = 'slx-toast show ' + (kind === 'err' ? 'err' : (kind === 'ok' ? 'ok' : ''));
        clearTimeout(el._t);
        el._t = setTimeout(function () { el.className = 'slx-toast'; }, 3200);
    }

    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    function confirmDialog(opts) {
        opts = opts || {};
        return new Promise(function (resolve) {
            var back = document.createElement('div');
            back.style.cssText = 'position:fixed;inset:0;background:rgba(15,23,42,.55);-webkit-backdrop-filter:blur(6px);backdrop-filter:blur(6px);display:flex;align-items:center;justify-content:center;z-index:5000;padding:1rem;';
            var box = document.createElement('div');
            box.style.cssText = 'background:var(--surface,#fff);border-radius:16px;padding:1.5rem 1.75rem;max-width:440px;width:100%;box-shadow:0 25px 70px rgba(0,0,0,.4);text-align:center;';
            box.innerHTML =
                '<div style="font-size:2rem;line-height:1;margin-bottom:.5rem;">' + (opts.icon || '\u26a0\ufe0f') + '</div>' +
                '<h3 style="margin:0 0 .5rem;font-size:1.15rem;font-weight:800;color:var(--text);">' + esc(opts.title || 'Are you sure?') + '</h3>' +
                '<p style="color:var(--slx-muted,#64748b);font-size:.9rem;line-height:1.55;margin:0 0 1.1rem;white-space:pre-line;">' + (opts.message || '') + '</p>' +
                '<div style="display:flex;gap:.6rem;justify-content:center;">' +
                    '<button type="button" data-r="0" style="min-width:110px;padding:.55rem 1.1rem;border-radius:10px;border:1px solid var(--slx-border,#e5e9f0);background:var(--slx-surface-2,#f8fafc);color:var(--text);font-weight:700;font-size:.85rem;cursor:pointer;">' + esc(opts.noLabel || 'Cancel') + '</button>' +
                    '<button type="button" data-r="1" style="min-width:110px;padding:.55rem 1.1rem;border-radius:10px;border:none;background:' + (opts.danger ? '#dc2626' : '#4f46e5') + ';color:#fff;font-weight:700;font-size:.85rem;cursor:pointer;">' + esc(opts.yesLabel || 'Confirm') + '</button>' +
                '</div>';
            back.appendChild(box);
            document.body.appendChild(back);
            function cleanup(v) {
                if (back.parentNode) document.body.removeChild(back);
                document.removeEventListener('keydown', onKey);
                resolve(v);
            }
            function onKey(e) { if (e.key === 'Escape') cleanup(false); }
            document.addEventListener('keydown', onKey);
            back.addEventListener('click', function (e) {
                if (e.target === back) { cleanup(false); return; }
                var b = e.target.closest('button[data-r]');
                if (b) cleanup(b.getAttribute('data-r') === '1');
            });
        });
    }

    function openModal(id) {
        var el = document.getElementById(id);
        if (el) el.classList.add('show');
    }
    function closeModal(id) {
        var el = document.getElementById(id);
        if (el) el.classList.remove('show');
    }

    document.addEventListener('click', function (e) {
        var closer = e.target.closest('[data-close]');
        if (closer) { closeModal(closer.getAttribute('data-close')); return; }
        var back = e.target.closest('.slx-modal-backdrop');
        if (back && e.target === back) back.classList.remove('show');
    });
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            document.querySelectorAll('.slx-modal-backdrop.show').forEach(function (el) {
                el.classList.remove('show');
            });
        }
    });

    // ================== Assign Subjects ==================
    var asgCache = { rows: [], classes: [], subjects: [], teachers: [] };
    var asgEditingId = null;
    var asgLoaded = false;

    function fillSelect(el, items, placeholder) {
        if (!el) return;
        el.innerHTML = '';
        var opt0 = document.createElement('option');
        opt0.value = '';
        opt0.textContent = placeholder;
        el.appendChild(opt0);
        items.forEach(function (it) {
            var o = document.createElement('option');
            o.value = it.id;
            o.textContent = it.name + (it.job_title ? ' \u2014 ' + it.job_title : '');
            el.appendChild(o);
        });
    }

    function currentTeacherForSubject(classId, subjectId) {
        var cid = String(classId), sid = String(subjectId);
        for (var i = 0; i < asgCache.rows.length; i++) {
            var r = asgCache.rows[i];
            if (String(r.class_id) === cid && String(r.subject_id) === sid && r.is_active) {
                return r;
            }
        }
        return null;
    }

    function renderAssignments() {
        var tb = document.getElementById('slxAsgTbody');
        if (!tb) return;
        var needle = (document.getElementById('slxAsgSearch').value || '').trim().toLowerCase();
        var rows = asgCache.rows.filter(function (r) { return r.is_active; });
        if (needle) {
            rows = rows.filter(function (r) {
                return (r.class_name + ' ' + r.subject_name + ' ' + r.teacher_name).toLowerCase().indexOf(needle) !== -1;
            });
        }
        if (!rows.length) {
            tb.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--slx-muted);padding:1rem;">No assignments match.</td></tr>';
            return;
        }
        var html = '';
        rows.forEach(function (r) {
            html += '<tr data-row-id="' + r.id + '">'
                 +   '<td>' + esc(r.class_name) + '</td>'
                 +   '<td>' + esc(r.subject_name) + '</td>'
                 +   '<td>' + (r.teacher_name ? esc(r.teacher_name) : '<span style="color:var(--slx-muted);">\u2014 unassigned \u2014</span>') + '</td>'
                 +   '<td style="text-align:right; white-space:nowrap;">'
                 +     '<button type="button" class="slx-icon-btn slx-asg-edit" data-id="' + r.id + '" title="Load into form">Edit</button> '
                 +     (r.teacher_id ? '<button type="button" class="slx-icon-btn slx-asg-remove" data-id="' + r.id + '" title="Unassign teacher">Unassign</button>' : '')
                 +   '</td>'
                 + '</tr>';
        });
        tb.innerHTML = html;
    }

    function resetAsgForm() {
        asgEditingId = null;
        document.getElementById('slxAsgFormTitle').textContent = 'Add New Assignment';
        document.getElementById('slxAsgResetBtn').style.display = 'none';
        document.getElementById('slxAsgCurrentInfo').style.display = 'none';
        document.getElementById('slxAsgClass').value = '';
        document.getElementById('slxAsgSubject').value = '';
        document.getElementById('slxAsgTeacher').value = '';
    }

    function asgScrollAndHighlight() {
        var card = document.getElementById('slxAsgFormCard');
        if (!card) return;
        try { card.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
        catch (e) { try { card.scrollIntoView(); } catch (e2) {} }
        var prev = card.style.boxShadow;
        card.style.boxShadow = '0 0 0 3px rgba(79,70,229,0.35)';
        card.style.background = 'rgba(79,70,229,0.06)';
        setTimeout(function () {
            card.style.boxShadow = prev;
            card.style.background = '';
        }, 1800);
    }

    function updateCurrentInfo() {
        var cid = document.getElementById('slxAsgClass').value;
        var sid = document.getElementById('slxAsgSubject').value;
        var info = document.getElementById('slxAsgCurrentInfo');
        var span = document.getElementById('slxAsgCurrentTeacher');
        if (!cid || !sid) {
            info.style.display = 'none';
            return;
        }
        var hit = currentTeacherForSubject(cid, sid);
        if (hit && hit.teacher_id) {
            info.style.display = 'block';
            span.textContent = hit.teacher_name + ' (currently assigned to teach this subject)';
        } else {
            info.style.display = 'none';
        }
    }

    function loadAssignments(force) {
        if (asgLoaded && !force) return Promise.resolve();
        var loading = document.getElementById('slxAsgLoading');
        var wrapper = document.getElementById('slxAsgWrapper');
        loading.style.display = 'flex';
        wrapper.style.display = 'none';
        return fetch(URLS.asgList, { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (j) {
                if (!j.ok) { toast(j.error || 'Failed to load assignments', 'err'); return; }
                asgCache = j;
                asgLoaded = true;
                fillSelect(document.getElementById('slxAsgClass'), j.classes, '\u2014 Select Class \u2014');
                fillSelect(document.getElementById('slxAsgSubject'), j.subjects, '\u2014 Select Subject \u2014');
                fillSelect(document.getElementById('slxAsgTeacher'), j.teachers, '\u2014 Unassigned \u2014');
                renderAssignments();
                loading.style.display = 'none';
                wrapper.style.display = 'block';
            })
            .catch(function (e) {
                loading.style.display = 'none';
                toast('Network error: ' + e.message, 'err');
            });
    }

    function onAsgRowClick(e) {
        var editBtn = e.target.closest('.slx-asg-edit');
        var removeBtn = e.target.closest('.slx-asg-remove');

        if (editBtn) {
            var id = parseInt(editBtn.getAttribute('data-id'), 10);
            var row = asgCache.rows.find(function (r) { return r.id === id; });
            if (!row) return;
            asgEditingId = row.id;
            document.getElementById('slxAsgFormTitle').textContent = 'Edit Assignment';
            document.getElementById('slxAsgResetBtn').style.display = 'inline-flex';
            document.getElementById('slxAsgClass').value = String(row.class_id);
            document.getElementById('slxAsgSubject').value = String(row.subject_id);
            document.getElementById('slxAsgTeacher').value = row.teacher_id ? String(row.teacher_id) : '';
            updateCurrentInfo();
            asgScrollAndHighlight();
            return;
        }

        if (removeBtn) {
            var rid = parseInt(removeBtn.getAttribute('data-id'), 10);
            var row2 = asgCache.rows.find(function (r) { return r.id === rid; });
            if (!row2) return;
            confirmDialog({
                icon: '\ud83d\uddd1\ufe0f',
                title: 'Unassign teacher?',
                message: 'Remove ' + (row2.teacher_name || 'the teacher') + ' from "' + row2.subject_name + '" in ' + row2.class_name + '?',
                yesLabel: 'Yes, unassign',
                noLabel: 'Cancel',
                danger: true
            }).then(function (ok) {
                if (!ok) return;
                fetch(URLS.asgUnassign, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrf(),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ assignment_id: rid })
                })
                .then(function (r) { return r.json(); })
                .then(function (j) {
                    if (!j.ok) { toast(j.error || 'Failed to remove', 'err'); return; }
                    toast('Teacher unassigned.', 'ok');
                    loadAssignments(true);
                })
                .catch(function (e) { toast('Network error: ' + e.message, 'err'); });
            });
        }
    }

    function onAsgSave() {
        var cid = document.getElementById('slxAsgClass').value;
        var sid = document.getElementById('slxAsgSubject').value;
        var tid = document.getElementById('slxAsgTeacher').value;
        if (!cid || !sid) { toast('Pick a class and subject.', 'err'); return; }

        var cSel = document.getElementById('slxAsgClass');
        var sSel = document.getElementById('slxAsgSubject');
        var tSel = document.getElementById('slxAsgTeacher');
        var cName = cSel.options[cSel.selectedIndex] ? cSel.options[cSel.selectedIndex].text : '';
        var sName = sSel.options[sSel.selectedIndex] ? sSel.options[sSel.selectedIndex].text : '';
        var tName = tid ? (tSel.options[tSel.selectedIndex] ? tSel.options[tSel.selectedIndex].text : '') : '\u2014 unassigned \u2014';

        var existing = currentTeacherForSubject(cid, sid);
        var msg;
        if (existing && existing.teacher_id && String(existing.teacher_id) !== String(tid)) {
            msg = 'Replace "' + existing.teacher_name + '" with "' + tName + '" as the teacher for "' + sName + '" in ' + cName + '?';
        } else if (existing && !tid) {
            msg = 'Unassign the teacher from "' + sName + '" in ' + cName + '?';
        } else {
            msg = 'Assign "' + tName + '" to teach "' + sName + '" in ' + cName + '?';
        }

        confirmDialog({
            icon: '\ud83d\udcd8',
            title: existing && existing.teacher_id ? 'Confirm replacement' : 'Confirm assignment',
            message: msg,
            yesLabel: 'Yes, save',
            noLabel: 'Cancel'
        }).then(function (ok) {
            if (!ok) return;
            fetch(URLS.asgSave, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ class_id: cid, subject_id: sid, teacher_id: tid || null })
            })
            .then(function (r) { return r.json(); })
            .then(function (j) {
                if (!j.ok) { toast(j.error || 'Failed to save', 'err'); return; }
                toast('Assignment saved.', 'ok');
                resetAsgForm();
                loadAssignments(true);
            })
            .catch(function (e) { toast('Network error: ' + e.message, 'err'); });
        });
    }

    document.getElementById('slxOpenSubjects').addEventListener('click', function () {
        openModal('slxSubjectsModal');
        resetAsgForm();
        loadAssignments(false);
    });
    document.getElementById('slxAsgSearch').addEventListener('input', renderAssignments);
    document.getElementById('slxAsgTbody').addEventListener('click', onAsgRowClick);
    document.getElementById('slxAsgSave').addEventListener('click', onAsgSave);
    document.getElementById('slxAsgResetBtn').addEventListener('click', function () {
        resetAsgForm();
    });
    document.getElementById('slxAsgReplaceBtn').addEventListener('click', function () {
        document.getElementById('slxAsgTeacher').focus();
    });
    document.getElementById('slxAsgClass').addEventListener('change', updateCurrentInfo);
    document.getElementById('slxAsgSubject').addEventListener('change', updateCurrentInfo);

    // ================== Manage Class Teachers ==================
    var ctCache = { rows: [], candidates: [] };
    var ctLoaded = false;

    function ctCandidateLabel(c) {
        var parts = [c.name];
        if (c.job_title) parts.push('\u2014 ' + c.job_title);
        var tail = [];
        if (c.subjects) tail.push('subjects: ' + c.subjects);
        if (c.is_class_teacher_of && c.is_class_teacher_of.length) {
            tail.push('currently CT of ' + c.is_class_teacher_of.join(', '));
        }
        return parts.join(' ') + (tail.length ? '  [' + tail.join(' | ') + ']' : '');
    }

    function renderClassTeachers() {
        var tb = document.getElementById('slxCtTbody');
        var empty = document.getElementById('slxCtEmpty');
        if (!tb) return;
        var needle = (document.getElementById('slxCtSearch').value || '').trim().toLowerCase();
        var rows = ctCache.rows;
        if (needle) {
            rows = rows.filter(function (r) {
                return (r.name + ' ' + (r.class_teacher_name || '')).toLowerCase().indexOf(needle) !== -1;
            });
        }
        document.getElementById('slxCtCount').textContent = (ctCache.candidates || []).length;
        if (!ctCache.candidates || !ctCache.candidates.length) {
            tb.innerHTML = '';
            empty.style.display = 'block';
            return;
        }
        empty.style.display = 'none';
        if (!rows.length) {
            tb.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--slx-muted);padding:1rem;">No classes match.</td></tr>';
            return;
        }
        var html = '';
        rows.forEach(function (r) {
            var ctName = r.class_teacher_name || '\u2014 unassigned \u2014';
            var ctExtra = '';
            if (r.class_teacher_id) {
                var m = ctCache.candidates.filter(function (c) { return c.id === r.class_teacher_id; })[0];
                if (m && m.subjects) {
                    ctExtra = ' <span style="color:var(--slx-muted); font-weight:400;">(' + esc(m.subjects) + ')</span>';
                }
            }
            html += '<tr data-class-id="' + r.id + '">'
                 +   '<td><strong>' + esc(r.name) + '</strong></td>'
                 +   '<td style="text-align:center;">' + (r.student_count || 0) + '</td>'
                 +   '<td>' + (r.class_teacher_id ? ctName + ctExtra : '<span style="color:var(--slx-muted);">' + ctName + '</span>') + '</td>'
                 +   '<td>'
                 +     '<select class="slx-ct-select" data-class-id="' + r.id + '" data-prev="' + (r.class_teacher_id || '') + '">'
                 +       '<option value="">\u2014 Unassign \u2014</option>';
            ctCache.candidates.forEach(function (c) {
                var sel = (r.class_teacher_id && c.id === r.class_teacher_id) ? ' selected' : '';
                html += '<option value="' + c.id + '"' + sel + '>' + esc(ctCandidateLabel(c)) + '</option>';
            });
            html += '</select></td></tr>';
        });
        tb.innerHTML = html;
    }

    function loadClassTeachers(force) {
        if (ctLoaded && !force) return Promise.resolve();
        var loading = document.getElementById('slxCtLoading');
        var wrapper = document.getElementById('slxCtWrapper');
        loading.style.display = 'flex';
        wrapper.style.display = 'none';
        return fetch(URLS.ctList, { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (j) {
                if (!j.ok) { toast(j.error || 'Failed to load', 'err'); return; }
                ctCache = j;
                ctLoaded = true;
                renderClassTeachers();
                loading.style.display = 'none';
                wrapper.style.display = 'block';
            })
            .catch(function (e) {
                loading.style.display = 'none';
                toast('Network error: ' + e.message, 'err');
            });
    }

    function onCtChange(e) {
        var sel = e.target.closest('.slx-ct-select');
        if (!sel) return;
        var classId = parseInt(sel.getAttribute('data-class-id'), 10);
        var teacherId = sel.value;
        var prevVal = sel.getAttribute('data-prev') || '';
        var tr = sel.closest('tr');
        var cName = tr && tr.querySelector('td strong') ? tr.querySelector('td strong').textContent : 'this class';
        var tName = teacherId ? sel.options[sel.selectedIndex].text : '\u2014 unassign \u2014';

        var message;
        if (!teacherId) {
            message = 'Remove the class teacher from "' + cName + '"?';
        } else {
            var cand = ctCache.candidates.filter(function (c) { return String(c.id) === String(teacherId); })[0];
            var extras = [];
            if (cand && cand.subjects) extras.push('subjects: ' + cand.subjects);
            if (cand && cand.is_class_teacher_of && cand.is_class_teacher_of.length) {
                extras.push('\u26a0 currently class teacher of ' + cand.is_class_teacher_of.join(', '));
            }
            message = 'Set "' + tName + '" as class teacher of "' + cName + '"?' +
                      (extras.length ? '\n\n' + extras.join('\n') : '');
        }

        confirmDialog({
            icon: teacherId ? '\ud83d\udc64' : '\ud83d\uddd1\ufe0f',
            title: teacherId ? 'Confirm class teacher change' : 'Remove class teacher',
            message: message,
            yesLabel: teacherId ? 'Yes, assign' : 'Yes, unassign',
            noLabel: 'Cancel',
            danger: !teacherId
        }).then(function (ok) {
            if (!ok) { sel.value = prevVal; return; }
            fetch(URLS.ctSave, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ class_id: classId, teacher_id: teacherId || null })
            })
            .then(function (r) { return r.json(); })
            .then(function (j) {
                if (!j.ok) { toast(j.error || 'Failed to save', 'err'); sel.value = prevVal; return; }
                toast('Class teacher updated.', 'ok');
                loadClassTeachers(true);
            })
            .catch(function (er) {
                toast('Network error: ' + er.message, 'err');
                sel.value = prevVal;
            });
        });
    }

    document.getElementById('slxOpenClassTeachers').addEventListener('click', function () {
        openModal('slxClassTeachersModal');
        loadClassTeachers(false);
    });
    document.getElementById('slxCtSearch').addEventListener('input', renderClassTeachers);
    document.getElementById('slxCtTbody').addEventListener('change', onCtChange);

    // ================== Fixtures ==================
    var fixCache = { assignments: [], isHoliday: false };

    function loadFixtures() {
        var loading = document.getElementById('slxFixLoading');
        var wrapper = document.getElementById('slxFixWrapper');
        var meta = document.getElementById('slxFixMeta');
        loading.style.display = 'flex';
        wrapper.style.display = 'none';
        meta.textContent = 'Loading\u2026';
        return fetch(URLS.fixtures, { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (j) {
                loading.style.display = 'none';
                if (!j.success) { toast(j.error || 'Failed to load fixtures', 'err'); return; }
                fixCache.assignments = j.assignments || [];
                fixCache.isHoliday = !!j.is_holiday;
                meta.textContent = (j.day_name || '') + ' \u2022 ' + (j.date || '') +
                                   ' \u2022 ' + (j.on_leave_count || 0) + ' teacher(s) on leave';

                if (j.is_holiday) {
                    wrapper.innerHTML =
                        '<div style="padding:2rem 1rem;text-align:center;">' +
                            '<div style="font-size:2.5rem;line-height:1;margin-bottom:.5rem;">\ud83c\udf89</div>' +
                            '<h3 style="margin:0 0 .25rem;">Holiday</h3>' +
                            '<p style="color:var(--slx-muted);">' + esc(j.holiday_reason || 'Today is a holiday.') + '</p>' +
                        '</div>';
                    wrapper.style.display = 'block';
                    return;
                }

                var list = fixCache.assignments;
                if (!list.length) {
                    wrapper.innerHTML =
                        '<div style="padding:2rem 1rem;text-align:center;">' +
                            '<div style="font-size:2.5rem;line-height:1;margin-bottom:.5rem;">\u2705</div>' +
                            '<h3 style="margin:0 0 .25rem;">Nothing to cover today</h3>' +
                            '<p style="color:var(--slx-muted);">No teacher on approved leave has a period scheduled for today.</p>' +
                        '</div>';
                    wrapper.style.display = 'block';
                    return;
                }

                var html = '';
                list.forEach(function (a, idx) {
                    var existing = a.existing_substitute;
                    var subLine = '';
                    var actionHtml = '';

                    if (existing) {
                        subLine = '<div style="font-size:.78rem;color:#047857;font-weight:700;margin-top:.3rem;">\u2713 Covered by ' + esc(existing.teacher_name) + '</div>';
                        actionHtml = '<button type="button" class="slx-btn slx-btn-danger slx-fix-remove" data-id="' + existing.id + '">Remove</button>';
                    } else if (!a.free_teachers || !a.free_teachers.length) {
                        subLine = '<div style="font-size:.78rem;color:#b91c1c;margin-top:.3rem;">No free teacher available at this period.</div>';
                    } else {
                        var opts = '<option value="">\u2014 Pick substitute \u2014</option>';
                        a.free_teachers.forEach(function (t) {
                            opts += '<option value="' + t.id + '">' + esc(t.name) + (t.job_title ? ' \u2014 ' + esc(t.job_title) : '') + '</option>';
                        });
                        subLine = '<div style="display:flex;gap:.5rem;margin-top:.5rem;flex-wrap:wrap;">' +
                                  '<select class="slx-select slx-fix-pick" data-idx="' + idx + '" style="height:36px;max-width:260px;">' + opts + '</select>';
                        actionHtml = '<button type="button" class="slx-btn slx-btn-primary slx-fix-assign" data-idx="' + idx + '" style="height:36px;color:#fff;">Assign</button></div>';
                    }

                    html += '<div style="border:1px solid var(--slx-border);border-radius:12px;padding:.85rem 1rem;margin-bottom:.6rem;background:var(--slx-surface-2);">' +
                              '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;flex-wrap:wrap;">' +
                                '<div style="flex:1;min-width:220px;">' +
                                  '<div style="font-weight:800;font-size:.9rem;">P' + a.period_order + ' \u2022 ' + esc(a.class_display) + '</div>' +
                                  '<div style="font-size:.78rem;color:var(--slx-muted);margin-top:.15rem;">' +
                                    esc(a.absent_teacher_name) + ' (on leave)' +
                                    (a.subject_name ? ' \u2022 ' + esc(a.subject_name) : '') +
                                  '</div>' +
                                  subLine +
                                '</div>' +
                                '<div>' + actionHtml + '</div>' +
                              '</div>' +
                            '</div>';
                });
                wrapper.innerHTML = html;
                wrapper.style.display = 'block';
            })
            .catch(function (e) {
                loading.style.display = 'none';
                toast('Network error: ' + e.message, 'err');
            });
    }

    document.getElementById('slxOpenFixtures').addEventListener('click', function () {
        openModal('slxFixturesModal');
        loadFixtures();
    });

    document.getElementById('slxFixWrapper').addEventListener('click', function (e) {
        var assignBtn = e.target.closest('.slx-fix-assign');
        var removeBtn = e.target.closest('.slx-fix-remove');
        var wrapper = document.getElementById('slxFixWrapper');

        if (assignBtn) {
            var idx = parseInt(assignBtn.getAttribute('data-idx'), 10);
            var sel = wrapper.querySelector('.slx-fix-pick[data-idx="' + idx + '"]');
            var subId = sel ? sel.value : '';
            if (!subId) { toast('Pick a substitute first.', 'err'); return; }
            var a = fixCache.assignments[idx];
            if (!a) return;
            var subName = sel.options[sel.selectedIndex] ? sel.options[sel.selectedIndex].text : 'this teacher';
            confirmDialog({
                icon: '\ud83d\udd01',
                title: 'Confirm fixture',
                message: 'Assign "' + subName + '" to cover P' + a.period_order + ' ' + a.class_display + ' for ' + a.absent_teacher_name + '?',
                yesLabel: 'Yes, assign',
                noLabel: 'Cancel'
            }).then(function (ok) {
                if (!ok) return;
                fetch(URLS.subCreate, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrf(),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        absent_teacher_id: a.absent_teacher_id,
                        substitute_teacher_id: parseInt(subId, 10),
                        class_id: a.class_id,
                        subject_id: a.subject_id,
                        period_order: a.period_order
                    })
                })
                .then(function (r) { return r.json(); })
                .then(function (j) {
                    if (!j.success) { toast(j.error || 'Failed', 'err'); return; }
                    toast('Substitute assigned.', 'ok');
                    loadFixtures();
                })
                .catch(function (er) { toast('Network error: ' + er.message, 'err'); });
            });
        }

        if (removeBtn) {
            var id = parseInt(removeBtn.getAttribute('data-id'), 10);
            confirmDialog({
                icon: '\ud83d\uddd1\ufe0f',
                title: 'Remove substitute',
                message: 'Remove this substitute assignment for today?',
                yesLabel: 'Yes, remove',
                noLabel: 'Cancel',
                danger: true
            }).then(function (ok) {
                if (!ok) return;
                fetch(URLS.subDelete, {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrf(),
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ id: id })
                })
                .then(function (r) { return r.json(); })
                .then(function (j) {
                    if (!j.success) { toast(j.error || 'Failed', 'err'); return; }
                    toast('Substitute removed.', 'ok');
                    loadFixtures();
                })
                .catch(function (er) { toast('Network error: ' + er.message, 'err'); });
            });
        }
    });
})();
</script>
{% endblock %}
"""


def patch_staff_list_template(root, dry):
    path = root / 'templates' / 'tenant' / 'staff_list.html'
    text = _read(path)
    if text is None:
        warn('staff_list.html not found')
        return

    if 'STAFF_LIST_UX_OVERHAUL_V1' in text:
        info('staff_list.html already patched')
        return

    start_anchor = '<!-- ================= Modal: Assign Subjects ================= -->'
    end_anchor = '<div class="slx-toast" id="slxToast"></div>'
    if start_anchor not in text or end_anchor not in text:
        warn('staff_list.html: modal anchors missing, skipping modal rebuild')
    else:
        new_text, problem = _replace_between(text, start_anchor, end_anchor, NEW_MODALS)
        if problem:
            warn('staff_list.html modals: %s', problem)
        else:
            text = new_text

    s_start = text.find('{% block extra_scripts %}')
    if s_start < 0:
        warn('staff_list.html: extra_scripts block missing')
    else:
        s_end = text.rfind('{% endblock %}')
        if s_end < s_start:
            warn('staff_list.html: end of extra_scripts block not found')
        else:
            text = text[:s_start] + NEW_SCRIPT + text[s_end + len('{% endblock %}') :]

    _write(path, text, dry)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description='STAFF_LIST_UX_OVERHAUL_V1')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--verbose', action='store_true')
    ap.add_argument('--target-dir', default='.')
    args = ap.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(message)s',
    )

    root = Path(args.target_dir).resolve()
    info('target: %s', root)
    info('dry-run: %s', args.dry_run)

    patch_helpers(root, args.dry_run)
    patch_assign_teachers(root, args.dry_run)
    patch_staff_extras(root, args.dry_run)
    patch_staff_list_template(root, args.dry_run)

    info('running post-patch automation')
    _run_command(root, [sys.executable, 'manage.py', 'check'], args.dry_run)
    _run_command(
        root,
        [sys.executable, 'manage.py', 'shell', '-c',
         'from django.core.cache import cache; cache.clear()'],
        args.dry_run,
    )

    info('done')


if __name__ == '__main__':
    sys.exit(main())
