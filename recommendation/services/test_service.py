import re

from django.db import transaction

from recommendation.dto import SaveWeightsDTO
from recommendation.models import QuestionOption
from recommendation.repository import save_weight_items


_OPTION_KEY_RE = re.compile(
    r'^options-(?P<question_index>\d+)-(?P<option_index>\d+)-'
    r'(?P<field>id|icon|option_text_fa|option_text_en|order)$'
)


class TestService:
    @staticmethod
    def _extract_option_rows(post_data, question_index):
        """
        Extract the custom nested option payload for one question.

        The current templates do not use a real nested formset, so we must parse
        keys such as ``options-0-1-option_text_fa`` manually. A hidden option
        ``id`` is supported when the template provides it, but the synchroniser
        also preserves existing rows by text/order when it is absent.
        """
        rows = {}
        payload_present = False

        total_forms_key = f'options-{question_index}-TOTAL_FORMS'
        if total_forms_key in post_data:
            payload_present = True

        for key, value in post_data.items():
            match = _OPTION_KEY_RE.match(key)
            if not match or int(match.group('question_index')) != question_index:
                continue

            payload_present = True
            option_index = int(match.group('option_index'))
            field_name = match.group('field')
            rows.setdefault(option_index, {})[field_name] = value

        normalized_rows = []
        for option_index in sorted(rows):
            row = rows[option_index]
            fa = str(row.get('option_text_fa') or '').strip()
            en = str(row.get('option_text_en') or '').strip()
            icon = str(row.get('icon') or '').strip()
            raw_id = str(row.get('id') or '').strip()
            raw_order = str(row.get('order') or '').strip()

            try:
                option_id = int(raw_id) if raw_id else None
            except (TypeError, ValueError):
                option_id = None

            try:
                order = int(raw_order) if raw_order else option_index + 1
            except (TypeError, ValueError):
                order = option_index + 1

            normalized_rows.append({
                'index': option_index,
                'id': option_id,
                'icon': icon,
                'option_text_fa': fa,
                'option_text_en': en,
                'order': max(1, order),
                'is_blank': not fa and not en,
            })

        return normalized_rows, payload_present

    @staticmethod
    def _find_existing_option(row, existing_options, used_ids):
        """Find the existing option that should be updated instead of replaced."""
        existing_by_id = {option.id: option for option in existing_options}

        option_id = row.get('id')
        if option_id and option_id in existing_by_id and option_id not in used_ids:
            return existing_by_id[option_id]

        # Exact text matching safely handles option reordering when no hidden id
        # is posted by the current custom template.
        row_fa = row.get('option_text_fa') or ''
        row_en = row.get('option_text_en') or ''
        for option in existing_options:
            if option.id in used_ids:
                continue
            option_fa = str(getattr(option, 'option_text_fa', '') or '').strip()
            option_en = str(getattr(option, 'option_text_en', '') or '').strip()
            if option_fa == row_fa and option_en == row_en:
                return option

        # Fallback to the option in the same visual position. This preserves the
        # primary key (and therefore weights) when an option's text is edited.
        row_index = row.get('index', 0)
        if 0 <= row_index < len(existing_options):
            candidate = existing_options[row_index]
            if candidate.id not in used_ids:
                return candidate

        return None

    @classmethod
    def _sync_question_options(cls, question, question_index, post_data, *, preserve_if_missing=True):
        """
        Update options in place so OptionScaleWeight rows are never lost merely
        because a question or option text was edited.
        """
        rows, payload_present = cls._extract_option_rows(post_data, question_index)

        # If the edit form did not submit option controls at all, leave existing
        # options untouched rather than interpreting the missing payload as delete.
        if preserve_if_missing and not payload_present:
            return

        existing_options = list(question.options.all().order_by('order', 'id'))
        used_ids = set()

        for row in rows:
            if row['is_blank']:
                continue

            option = cls._find_existing_option(row, existing_options, used_ids)
            if option is None:
                option = QuestionOption(question=question)

            option.icon = row['icon']
            option.option_text_fa = row['option_text_fa']
            option.option_text_en = row['option_text_en']
            option.order = row['order']
            option.save()
            used_ids.add(option.id)

        # Delete only options that the submitted form explicitly removed. Their
        # own weights are deleted by cascade, but every untouched option keeps its
        # original primary key and all OptionScaleWeight records.
        if payload_present:
            question.options.exclude(id__in=used_ids).delete()

    @classmethod
    @transaction.atomic
    def create_test(cls, form, question_formset, scale_formset, post_data):
        test = form.save()
        question_formset.save(commit=False)

        for index, question_form in enumerate(question_formset.forms):
            cleaned_data = getattr(question_form, 'cleaned_data', None) or {}
            if not cleaned_data or cleaned_data.get('DELETE'):
                continue

            question = question_form.save(commit=False)
            question.test = test
            question.save()
            cls._sync_question_options(
                question,
                index,
                post_data,
                preserve_if_missing=False,
            )

        for obj in question_formset.deleted_objects:
            obj.delete()

        for scale in scale_formset.save(commit=False):
            scale.test = test
            scale.save()

        for obj in scale_formset.deleted_objects:
            obj.delete()

        return test

    @classmethod
    @transaction.atomic
    def update_test(cls, test, form, question_formset, scale_formset, post_data):
        form.save()
        question_formset.save(commit=False)

        # Do not call question.options.all().delete(). Deleting all options was
        # the exact reason every OptionScaleWeight row disappeared on each edit.
        for index, question_form in enumerate(question_formset.forms):
            cleaned_data = getattr(question_form, 'cleaned_data', None) or {}
            if not cleaned_data or cleaned_data.get('DELETE'):
                continue

            question = question_form.save(commit=False)
            question.test = test
            question.save()
            cls._sync_question_options(question, index, post_data)

        for obj in question_formset.deleted_objects:
            obj.delete()

        for scale in scale_formset.save(commit=False):
            scale.test = test
            scale.save()

        for obj in scale_formset.deleted_objects:
            obj.delete()

        return test

    @staticmethod
    def save_weights(dto: SaveWeightsDTO):
        if not dto.items:
            return 0

        for item in dto.items:
            if item.weight < 0:
                raise ValueError('Weight cannot be negative')

        return save_weight_items(dto.items)
