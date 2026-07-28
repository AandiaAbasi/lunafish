"""
Utility functions for Adviser app - School context management.
"""
from django.utils.translation import gettext_lazy as _



def calculate_test_result(student_response):
    """
    Calculate psychological test results for a student response.
    
    This function:
    1. Aggregates weights from selected options for each scale
    2. Generates summary (top scales, Holland code, etc.)
    3. Matches interpretations based on score ranges
    4. Creates or updates TestResult record
    
    Args:
        student_response: StudentTestResponse object (must be COMPLETED)
    
    Returns:
        TestResult object with calculated scores
    """
    from recommendation.models import (
        TestResult, StudentAnswer, OptionScaleWeight, 
        TestScale, ScaleInterpretation
    )
    from django.utils import timezone
    
    # Verify response is completed
    if student_response.status != 'completed':
        raise ValueError(_('فقط پاسخ‌های تکمیل شده قابل محاسبه هستند'))
    
    test = student_response.test
    
    # Get all scales for this test
    scales = TestScale.objects.filter(test=test).order_by('code')
    
    # If no scales defined, return empty result (simple test without scoring)
    if not scales.exists():
        result, created = TestResult.objects.update_or_create(
            response=student_response,
            defaults={
                'raw_scores': {},
                'summary': {
                    'message': 'این تست بدون سیستم امتیازدهی است',
                    'has_scales': False
                },
                'calculated_at': timezone.now()
            }
        )
        return result
    
    # Initialize score dictionary
    scale_scores = {scale.code: 0.0 for scale in scales}
    
    # Get all answers for this response
    answers = StudentAnswer.objects.filter(
        response=student_response,
        selected_option__isnull=False  # Only multiple choice answers
    ).select_related('selected_option', 'question')
    
    # Aggregate weights
    for answer in answers:
        # Get all weights for this selected option
        weights = OptionScaleWeight.objects.filter(
            option=answer.selected_option
        ).select_related('scale')
        
        for weight_obj in weights:
            scale_code = weight_obj.scale.code
            if scale_code in scale_scores:
                scale_scores[scale_code] += weight_obj.weight
    
    # Round scores to 2 decimal places
    scale_scores = {k: round(v, 2) for k, v in scale_scores.items()}
    
    # This application now stores only English placement tests. Never generate
    # Holland-style fields such as holland_code/top_3_scales for these results.
    summary = generate_english_placement_summary(scale_scores, scales)
    
    # Match interpretations
    interpretations = match_interpretations(scale_scores, scales)
    summary['interpretations'] = interpretations
    
    # Create or update TestResult
    result, created = TestResult.objects.update_or_create(
        response=student_response,
        defaults={
            'raw_scores': scale_scores,
            'summary': summary,
            'calculated_at': timezone.now()
        }
    )
    
    return result



def generate_english_placement_summary(scale_scores, scales):
    """Build CEFR placement and skill scores from configured scale metadata."""
    from recommendation.models import EnglishPlacementAssessment, TestScale

    scales = list(scales)
    level_rank_map = {
        'A1': 1,
        'A2': 2,
        'B1': 3,
        'B2': 4,
        'C1': 5,
        'C2': 6,
    }
    skill_codes = {'GRAM', 'VOCAB', 'READ', 'USE'}

    # Explicit metadata is preferred. Known codes are accepted as a safe fallback
    # so an already-created placement test does not become unusable after deploy.
    level_scales = [
        scale for scale in scales
        if scale.scale_type == TestScale.ScaleType.LEVEL
        or scale.code.strip().upper() in level_rank_map
    ]
    level_scales.sort(
        key=lambda scale: (
            scale.rank or level_rank_map.get(scale.code.strip().upper(), 999),
            scale.code,
        )
    )
    skill_scales = [
        scale for scale in scales
        if scale.scale_type == TestScale.ScaleType.SKILL
        or scale.code.strip().upper() in skill_codes
    ]

    suggested_level = EnglishPlacementAssessment.EnglishLevel.PRE_A1
    passed_levels = []
    valid_levels = {value for value, _ in EnglishPlacementAssessment.EnglishLevel.choices}

    # Levels are sequential. Once a level is failed, higher levels are not used
    # as the final placement even if a lucky score is higher there.
    for scale in level_scales:
        normalized_code = scale.code.strip().upper()
        score = float(scale_scores.get(scale.code, 0) or 0)
        pass_score = float(scale.pass_score)

        # Backward-compatible default for an old A1 scale that has not been
        # configured through the new admin fields yet.
        if scale.scale_type == TestScale.ScaleType.GENERAL and normalized_code == 'A1':
            pass_score = 60.0

        if score < pass_score:
            break

        level_value = normalized_code.lower().replace('-', '_')
        if level_value in valid_levels:
            suggested_level = level_value
            passed_levels.append(normalized_code)

    return {
        'has_scales': True,
        'result_type': 'english_placement',
        'suggested_level': suggested_level,
        'passed_levels': passed_levels,
        'level_scores': {
            scale.code: scale_scores.get(scale.code, 0)
            for scale in level_scales
        },
        'skill_scores': {
            scale.code: scale_scores.get(scale.code, 0)
            for scale in skill_scales
        },
        'scale_details': [
            {
                'code': scale.code,
                'title': scale.title,
                'score': scale_scores.get(scale.code, 0),
                'percentage': scale_scores.get(scale.code, 0),
                'scale_type': scale.scale_type,
                'pass_score': (
                    60.0
                    if scale.scale_type == TestScale.ScaleType.GENERAL
                    and scale.code.strip().upper() == 'A1'
                    else scale.pass_score
                ),
                'rank': scale.rank or level_rank_map.get(scale.code.strip().upper()),
                'description': scale.description,
            }
            for scale in sorted(
                scales,
                key=lambda item: (
                    item.code.strip().upper() not in level_rank_map,
                    item.rank or level_rank_map.get(item.code.strip().upper(), 999),
                    item.code,
                ),
            )
        ],
    }

def generate_test_summary(scale_scores, scales):
    """
    Generate summary information from scale scores.
    
    Creates:
    - Top N scales (for Holland code generation)
    - Score percentages
    - Ranking
    
    Args:
        scale_scores: Dict of {scale_code: score}
        scales: QuerySet of TestScale objects
    
    Returns:
        Dict with summary information
    """
    # Sort scales by score (descending)
    sorted_scales = sorted(scale_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Get top 3 scales for Holland code
    top_3_codes = [code for code, score in sorted_scales[:3]]
    holland_code = ''.join(top_3_codes)
    
    # Create scale details with titles
    scale_details = []
    scale_map = {scale.code: scale for scale in scales}
    
    for code, score in sorted_scales:
        if code in scale_map:
            scale_details.append({
                'code': code,
                'title': scale_map[code].title,
                'score': score,
                'description': scale_map[code].description
            })
    
    # Calculate total and percentages (if all scores are positive)
    total_score = sum(scale_scores.values())
    if total_score > 0:
        for detail in scale_details:
            detail['percentage'] = round((detail['score'] / total_score) * 100, 1)
    else:
        for detail in scale_details:
            detail['percentage'] = 0
    
    summary = {
        'has_scales': True,
        'holland_code': holland_code,
        'top_3_scales': top_3_codes,
        'scale_details': scale_details,
        'highest_scale': {
            'code': sorted_scales[0][0],
            'title': scale_map[sorted_scales[0][0]].title if sorted_scales[0][0] in scale_map else '',
            'score': sorted_scales[0][1]
        } if sorted_scales else None
    }
    
    return summary


def match_interpretations(scale_scores, scales):
    """
    Match score ranges to interpretations for each scale.
    
    Args:
        scale_scores: Dict of {scale_code: score}
        scales: QuerySet of TestScale objects
    
    Returns:
        Dict of {scale_code: [matched_interpretations]}
    """
    from recommendation.models import ScaleInterpretation
    
    interpretations = {}
    
    for scale in scales:
        score = scale_scores.get(scale.code, 0)
        
        # Get all interpretations for this scale
        scale_interpretations = ScaleInterpretation.objects.filter(
            scale=scale
        ).order_by('order', 'min_score')
        
        # Find matching interpretations (score falls within range)
        matched = []
        for interp in scale_interpretations:
            if interp.min_score <= score <= interp.max_score:
                matched.append({
                    'title': interp.title,
                    'description': interp.description,
                    'score_range': f'{interp.min_score} - {interp.max_score}',
                    'order': interp.order
                })
        
        if matched:
            interpretations[scale.code] = matched
    
    return interpretations


def recalculate_all_test_results(test):
    """
    Recalculate results for all completed responses to a test.
    
    Useful when:
    - Scales are modified
    - Weights are updated
    - Interpretations are changed
    
    Args:
        test: PsychologicalTest object
    
    Returns:
        Tuple of (success_count, error_count)
    """
    from recommendation.models import StudentTestResponse
    
    completed_responses = StudentTestResponse.objects.filter(
        test=test,
        status='completed'
    )
    
    success_count = 0
    error_count = 0
    
    for response in completed_responses:
        try:
            calculate_test_result(response)
            success_count += 1
        except Exception as e:
            error_count += 1
            print(f"Error calculating result for response {response.id}: {str(e)}")
    
    return success_count, error_count


def get_scale_statistics(test):
    """
    Get aggregate statistics for all scales in a test.
    
    Calculates:
    - Average score per scale
    - Min/max scores
    - Standard deviation
    - Distribution across interpretation ranges
    - Top scale (highest average)
    
    Args:
        test: PsychologicalTest object
    
    Returns:
        Dict with:
        - scales: {scale_code: {scale_obj, mean, std_dev, min, max, count, distribution}}
        - total_responses: Count of completed responses
        - top_scale: Scale object with highest average (or None)
    """
    from recommendation.models import TestResult, TestScale, ScaleInterpretation
    from django.db.models import Avg, Min, Max, Count
    
    scales = TestScale.objects.filter(test=test).prefetch_related('interpretations')
    
    # Get all results for this test
    results = TestResult.objects.filter(
        response__test=test,
        response__status='completed'
    )
    
    if not results.exists():
        return {
            'scales': {},
            'total_responses': 0,
            'top_scale': None
        }
    
    statistics = {
        'scales': {},
        'total_responses': results.count(),
        'top_scale': None
    }
    
    top_avg = -1
    
    for scale in scales:
        scale_scores = []
        interpretation_counts = {}  # {interpretation_id: count}
        
        # Collect scores and match to interpretations
        for result in results:
            score = result.raw_scores.get(scale.code)
            if score is not None:
                scale_scores.append(score)
                
                # Find matching interpretation
                matched_interp = None
                for interp in scale.interpretations.all():
                    if interp.min_score <= score <= interp.max_score:
                        matched_interp = interp
                        break
                
                if matched_interp:
                    interpretation_counts[matched_interp.id] = interpretation_counts.get(matched_interp.id, 0) + 1
        
        if scale_scores:
            mean_score = sum(scale_scores) / len(scale_scores)
            
            statistics['scales'][scale.code] = {
                'scale_obj': scale,
                'count': len(scale_scores),
                'mean': round(mean_score, 2),
                'min': round(min(scale_scores), 2),
                'max': round(max(scale_scores), 2),
                'distribution': interpretation_counts  # {interpretation_id: count}
            }
            
            # Calculate standard deviation
            if len(scale_scores) > 1:
                variance = sum((x - mean_score) ** 2 for x in scale_scores) / len(scale_scores)
                statistics['scales'][scale.code]['std_dev'] = round(variance ** 0.5, 2)
            else:
                statistics['scales'][scale.code]['std_dev'] = 0.0
            
            # Track top scale
            if mean_score > top_avg:
                top_avg = mean_score
                statistics['top_scale'] = scale
    
    return statistics



def debug_test_calculation(response_id):
    """
    Debug version of calculate_test_result that writes detailed logs to file.
    
    Args:
        response_id: ID of StudentTestResponse
    
    Returns:
        TestResult object
    """
    from recommendation.models import (
        StudentTestResponse, TestResult, TestScale, 
        OptionScaleWeight, StudentAnswer
    )
    
    response = StudentTestResponse.objects.get(id=response_id)
    test = response.test
    
    output_lines = []
    output_lines.append(f"=== Debug Test Calculation ===")
    output_lines.append(f"Response ID: {response.id}")
    output_lines.append(f"User: {response.user.name}")
    output_lines.append(f"Test: {test.title}")
    output_lines.append("")
    
    # Get all scales for this test
    scales = TestScale.objects.filter(test=test)
    output_lines.append(f"Found {scales.count()} scales:")
    for scale in scales:
        output_lines.append(f"  - {scale.code}: {scale.title}")
    output_lines.append("")
    
    # Get all student answers
    answers = StudentAnswer.objects.filter(response=response).select_related(
        'question', 'selected_option'
    )
    output_lines.append(f"Found {answers.count()} answers:")
    output_lines.append("")
    
    # Calculate scores per scale
    raw_scores = {}
    
    for scale in scales:
        output_lines.append(f"--- Calculating scale: {scale.code} ({scale.title}) ---")
        scale_score = 0.0
        
        for answer in answers:
            if answer.selected_option:
                # Get weight for this option-scale combination
                try:
                    weight_obj = OptionScaleWeight.objects.get(
                        option=answer.selected_option,
                        scale=scale
                    )
                    weight = weight_obj.weight
                    scale_score += weight
                    
                    output_lines.append(
                        f"  Q{answer.question.order}: "
                        f"Option '{answer.selected_option.option_text}' "
                        f"→ weight={weight} → running_total={scale_score}"
                    )
                except OptionScaleWeight.DoesNotExist:
                    output_lines.append(
                        f"  Q{answer.question.order}: "
                        f"Option '{answer.selected_option.option_text}' "
                        f"→ NO WEIGHT for scale {scale.code}"
                    )
        
        raw_scores[scale.code] = scale_score
        output_lines.append(f"  FINAL SCORE for {scale.code}: {scale_score}")
        output_lines.append("")
    
    # Sort scales by score
    sorted_scales = sorted(raw_scores.items(), key=lambda x: x[1], reverse=True)
    top_3 = sorted_scales[:3]
    holland_code = ''.join([code for code, score in top_3])
    
    output_lines.append("=== Final Results ===")
    output_lines.append(f"Raw scores: {raw_scores}")
    output_lines.append(f"Sorted: {sorted_scales}")
    output_lines.append(f"Top 3: {top_3}")
    output_lines.append(f"Holland code: {holland_code}")
    
    # Write to file
    output_path = '/tmp/test_debug.txt'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print(f"Debug output written to: {output_path}")
    
    # Create/update result
    summary = {
        'holland_code': holland_code,
        'top_scales': [code for code, score in top_3],
        'top_scores': [score for code, score in top_3]
    }
    
    result, created = TestResult.objects.update_or_create(
        response=response,
        defaults={
            'raw_scores': raw_scores,
            'summary': summary
        }
    )
    
    return result
