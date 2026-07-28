from recommendation.models import PsychologicalTest, OptionScaleWeight

def delete_test(test_id):
    """
    Deletes a PsychologicalTest by id.
    Returns True if something was deleted, else False.
    """
    deleted_count, _ = PsychologicalTest.objects.filter(id=test_id).delete()
    return deleted_count > 0


def save_weight_items(items):
    saved_count = 0

    for item in items:

        if item.weight == 0:
            # delete relation if weight is zero
            OptionScaleWeight.objects.filter(
                option_id=item.option_id,
                scale_id=item.scale_id
            ).delete()
            continue

        # update or create when weight is non-zero
        OptionScaleWeight.objects.update_or_create(
            option_id=item.option_id,
            scale_id=item.scale_id,
            defaults={"weight": item.weight}
        )

        saved_count += 1

    return saved_count