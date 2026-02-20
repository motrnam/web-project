# interrogation/utils.py
"""
Utility functions for calculating most wanted suspects and their rewards.
Based on the project requirements:
- Ranking = max(L_j) * max(D_i)
  where L_j = days wanted for crime j, D_i = severity of crime i (1-4)
- Reward = max(L_j) * max(D_i) * 20,000,000 Rials
"""
from django.utils import timezone
from django.db.models import Max, F, Q, ExpressionWrapper, fields
from datetime import timedelta
from .models import Suspect, SuspectStatus
from case.models import CrimeType


def get_crime_severity(crime_type):
    """
    Convert crime type to severity level (1-4).
    TYPE_3 -> 1, TYPE_2 -> 2, TYPE_1 -> 3, CRITICAL -> 4
    """
    severity_map = {
        CrimeType.TYPE_3: 1,
        CrimeType.TYPE_2: 2,
        CrimeType.TYPE_1: 3,
        CrimeType.CRITICAL: 4,
    }
    return severity_map.get(crime_type, 1)


def calculate_suspect_ranking(suspect):
    """
    Calculate ranking for a single suspect.
    Returns: (ranking_score, max_days, max_severity, reward_amount)
    """
    person = suspect.person
    
    # Get all suspects for this person (both open and closed cases)
    all_suspects = Suspect.objects.filter(person=person).select_related('case')
    
    max_days_wanted = 0
    max_severity = 0
    
    for s in all_suspects:
        # Calculate days wanted (only for WANTED or MOST_WANTED status)
        if s.suspect_status in [SuspectStatus.WANTED, SuspectStatus.MOST_WANTED]:
            days_wanted = (timezone.now() - s.added_at).days
            max_days_wanted = max(max_days_wanted, days_wanted)
        
        # Get crime severity
        severity = get_crime_severity(s.case.crime_type)
        max_severity = max(max_severity, severity)
    
    ranking = max_days_wanted * max_severity
    reward = ranking * 20_000_000  # Rials
    
    return ranking, max_days_wanted, max_severity, reward


def update_most_wanted_status():
    """
    Update suspect statuses based on how long they've been wanted.
    Suspects wanted for more than 30 days should be MOST_WANTED.
    """
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Find suspects who have been wanted for more than 30 days
    long_wanted = Suspect.objects.filter(
        suspect_status=SuspectStatus.WANTED,
        added_at__lte=thirty_days_ago
    )
    
    updated_count = long_wanted.update(suspect_status=SuspectStatus.MOST_WANTED)
    return updated_count


def get_most_wanted_list():
    """
    Get list of most wanted suspects with their rankings and rewards.
    Returns suspects sorted by ranking (highest first).
    """
    # First update statuses
    update_most_wanted_status()
    
    # Get all MOST_WANTED suspects
    most_wanted = Suspect.objects.filter(
        suspect_status=SuspectStatus.MOST_WANTED
    ).select_related('person', 'case').distinct()
    
    # Calculate rankings for each
    ranked_suspects = []
    for suspect in most_wanted:
        ranking, max_days, max_severity, reward = calculate_suspect_ranking(suspect)
        
        # Only include if they've actually been wanted for more than 30 days
        if max_days > 30:
            ranked_suspects.append({
                'suspect': suspect,
                'person': suspect.person,
                'ranking': ranking,
                'max_days_wanted': max_days,
                'max_crime_severity': max_severity,
                'reward_amount': reward,
                'cases_involved': Suspect.objects.filter(person=suspect.person).count()
            })
    
    # Sort by ranking (descending)
    ranked_suspects.sort(key=lambda x: x['ranking'], reverse=True)
    
    return ranked_suspects
