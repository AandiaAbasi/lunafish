from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe


LEVEL_CODES = ('A1', 'A2', 'B1', 'B2', 'C1', 'C2')
SKILL_CODES = ('GRAM', 'VOCAB', 'READ', 'USE')

LEVEL_LABELS = {
    'pre_a1': 'Pre-A1',
    'a1': 'A1',
    'a2': 'A2',
    'b1': 'B1',
    'b2': 'B2',
    'c1': 'C1',
    'c2': 'C2',
}

SKILL_LABELS = {
    'GRAM': 'گرامر',
    'VOCAB': 'واژگان',
    'READ': 'درک مطلب',
    'USE': 'کاربرد زبان',
}

DEFAULT_PASS_SCORES = {
    'A1': 60,
    'A2': 70,
    'B1': 70,
    'B2': 70,
    'C1': 70,
    'C2': 70,
}


def _safe_score(value):
    try:
        return max(0.0, min(100.0, float(value or 0)))
    except (TypeError, ValueError):
        return 0.0


def _level_label(value):
    if not value:
        return 'تعیین نشده'
    value = str(value).strip().lower()
    return LEVEL_LABELS.get(value, value.upper())


def _score_colour(score):
    if score >= 75:
        return '#16a34a'
    if score >= 60:
        return '#d97706'
    return '#dc2626'


def _infer_level(level_scores, pass_scores=None):
    pass_scores = pass_scores or DEFAULT_PASS_SCORES
    suggested = 'pre_a1'

    for code in LEVEL_CODES:
        if code not in level_scores:
            continue
        score = _safe_score(level_scores.get(code))
        if score < float(pass_scores.get(code, DEFAULT_PASS_SCORES.get(code, 70))):
            break
        suggested = code.lower()

    return suggested


def _build_detail_map(summary):
    details = {}
    for item in (summary or {}).get('scale_details', []) or []:
        code = str(item.get('code') or '').strip().upper()
        if code:
            details[code] = item
    return details


def _score_card(code, title, score, description='', pass_score=None):
    score = _safe_score(score)
    colour = _score_colour(score)
    threshold_html = ''
    if pass_score is not None:
        threshold_html = format_html(
            '<span style="font-size:11px;color:#6b7280;">حدنصاب: {}٪</span>',
            round(float(pass_score), 1),
        )

    return format_html(
        '<div style="border:1px solid #e5e7eb;border-radius:12px;padding:12px;background:#fff;min-width:210px;flex:1;">'
        '<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:8px;">'
        '<div><strong style="font-size:14px;">{}</strong> '
        '<span style="font-size:12px;color:#6b7280;">{}</span></div>'
        '<strong style="font-size:16px;color:{};direction:ltr;">{}٪</strong>'
        '</div>'
        '<div style="height:9px;background:#eef2f7;border-radius:999px;overflow:hidden;">'
        '<div style="width:{}%;height:100%;background:{};border-radius:999px;"></div>'
        '</div>'
        '<div style="display:flex;justify-content:space-between;gap:8px;margin-top:7px;">'
        '<span style="font-size:11px;color:#6b7280;line-height:1.7;">{}</span>{}'
        '</div>'
        '</div>',
        code,
        title,
        colour,
        round(score, 1),
        round(score, 1),
        colour,
        description or '',
        threshold_html,
    )


def render_placement_result(raw_scores=None, summary=None, final_level=None):
    raw_scores = raw_scores or {}
    summary = summary or {}
    detail_map = _build_detail_map(summary)

    level_scores = {
        code: _safe_score((summary.get('level_scores') or {}).get(code, raw_scores.get(code, 0)))
        for code in LEVEL_CODES
        if code in raw_scores or code in (summary.get('level_scores') or {}) or code in detail_map
    }
    skill_scores = {
        code: _safe_score((summary.get('skill_scores') or {}).get(code, raw_scores.get(code, 0)))
        for code in SKILL_CODES
        if code in raw_scores or code in (summary.get('skill_scores') or {}) or code in detail_map
    }

    pass_scores = {
        code: float(detail_map.get(code, {}).get('pass_score') or DEFAULT_PASS_SCORES[code])
        for code in level_scores
    }

    suggested = summary.get('suggested_level') or _infer_level(level_scores, pass_scores)
    is_legacy = summary.get('result_type') != 'english_placement'
    all_zero = bool(level_scores or skill_scores) and not any([*level_scores.values(), *skill_scores.values()])

    warning = ''
    if is_legacy:
        warning = mark_safe(
            '<div style="padding:10px 12px;border-radius:10px;background:#fff7ed;border:1px solid #fed7aa;color:#9a3412;margin-bottom:14px;">'
            'این نتیجه با ساختار قدیمی ذخیره شده است. گزینه «محاسبه مجدد نتیجه» را اجرا کنید.'
            '</div>'
        )
    elif all_zero:
        warning = mark_safe(
            '<div style="padding:10px 12px;border-radius:10px;background:#fef2f2;border:1px solid #fecaca;color:#991b1b;margin-bottom:14px;">'
            'تمام امتیازها صفر هستند. وزن گزینه‌های صحیح را بررسی کنید و سپس نتیجه را مجدداً محاسبه کنید.'
            '</div>'
        )

    final_badge = ''
    if final_level:
        final_badge = format_html(
            '<div style="padding:10px 16px;border-radius:12px;background:#ecfdf5;border:1px solid #a7f3d0;">'
            '<div style="font-size:11px;color:#047857;">سطح نهایی تأییدشده</div>'
            '<strong style="font-size:24px;color:#065f46;direction:ltr;display:block;">{}</strong>'
            '</div>',
            _level_label(final_level),
        )

    level_cards = format_html_join(
        '',
        '{}',
        ((
            _score_card(
                code,
                detail_map.get(code, {}).get('title', 'سطح زبان'),
                score,
                detail_map.get(code, {}).get('description', ''),
                pass_scores.get(code),
            ),
        ) for code, score in level_scores.items()),
    ) or mark_safe('<span style="color:#6b7280;">امتیاز سطحی ثبت نشده است.</span>')

    skill_cards = format_html_join(
        '',
        '{}',
        ((
            _score_card(
                code,
                detail_map.get(code, {}).get('title', SKILL_LABELS.get(code, code)),
                score,
                detail_map.get(code, {}).get('description', ''),
            ),
        ) for code, score in skill_scores.items()),
    ) or mark_safe('<span style="color:#6b7280;">امتیاز مهارتی ثبت نشده است.</span>')

    interpretations = summary.get('interpretations') or {}
    interpretation_items = []
    for code, items in interpretations.items():
        for item in items or []:
            interpretation_items.append((code, item))

    interpretations_html = ''
    if interpretation_items:
        interpretations_html = format_html(
            '<div style="margin-top:18px;">'
            '<h3 style="font-size:14px;margin:0 0 10px;">تفسیر نتیجه</h3>'
            '<div style="display:grid;gap:8px;">{}</div>'
            '</div>',
            format_html_join(
                '',
                '<div style="border-right:4px solid #2563eb;background:#eff6ff;padding:10px 12px;border-radius:8px;">'
                '<strong>{} — {}</strong><div style="color:#475569;margin-top:4px;line-height:1.8;">{}</div>'
                '</div>',
                ((
                    code,
                    item.get('title', ''),
                    item.get('description', ''),
                ) for code, item in interpretation_items),
            ),
        )

    return format_html(
        '<div style="max-width:1100px;direction:rtl;">'
        '{}'
        '<div style="display:flex;flex-wrap:wrap;gap:12px;margin-bottom:18px;">'
        '<div style="padding:10px 16px;border-radius:12px;background:#eff6ff;border:1px solid #bfdbfe;">'
        '<div style="font-size:11px;color:#1d4ed8;">سطح پیشنهادی سیستم</div>'
        '<strong style="font-size:24px;color:#1e3a8a;direction:ltr;display:block;">{}</strong>'
        '</div>{}'
        '</div>'
        '<h3 style="font-size:14px;margin:0 0 10px;">امتیاز سطح‌های CEFR</h3>'
        '<div style="display:flex;flex-wrap:wrap;gap:10px;">{}</div>'
        '<h3 style="font-size:14px;margin:20px 0 10px;">ارزیابی مهارت‌ها</h3>'
        '<div style="display:flex;flex-wrap:wrap;gap:10px;">{}</div>'
        '{}'
        '</div>',
        warning,
        _level_label(suggested),
        final_badge,
        level_cards,
        skill_cards,
        interpretations_html,
    )
