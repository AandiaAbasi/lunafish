from recommendation.models import ScaleInterpretation


class ScaleInterpretationRepository:

    @staticmethod
    def replace_scale_interpretations(scale, interpretations_data):
        """
        کل تفسیرها را حذف و دوباره ایجاد می‌کند.
        (توی فرمست‌های inline معمولاً این رفتار استاندارد است)
        
        interpretations_data = [
            {
                "id": 4 (optional),
                "min_score": 10,
                "max_score": 20,
                "title_fa": "...",
                "title_en": "...",
                "description_fa": "...",
                "description_en": "...", 
                "order": 1
            },
            ...
        ]
        """

        # حذف همه رکوردهای قبلی
        ScaleInterpretation.objects.filter(scale=scale).delete()

        # ایجاد رکوردهای جدید
        for item in interpretations_data:
            ScaleInterpretation.objects.create(
                scale=scale,
                title_fa=item.get("title_fa", ""),
                title_en=item.get("title_en", ""), 
                description_fa=item.get("description_fa", ""),
                description_en=item.get("description_en", ""), 
                order=item["order"],
                min_score=item["min_score"],
                max_score=item["max_score"],
            )
