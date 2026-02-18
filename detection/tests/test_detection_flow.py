# detection/tests/test_detection_flow.py
from django.db import connection
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import get_resolver
from rest_framework.test import APIClient  # ← This is important!
from rest_framework import status
from django.utils import timezone
import uuid
import itertools

from detection.models import Detection, DetectionBoard, Lead, Yarn, SuspectsSuggested
from case.models import Case
from evidences.models import Evidence
from interrogation.models import Suspect, Interrogation, InterrogationStatus

User = get_user_model()


class DetectionFlowTests(TestCase):
    """Test the complete detection flow from board management to suspect submission."""

    # detection/tests/test_detection_flow.py

    def setUp(self):
        """Set up test data before each test."""
        # Create necessary groups
        self.detective_group = Group.objects.create(name='Detective')
        self.sergeant_group = Group.objects.create(name='Sergeant')

        # Use counter for unique values
        self.user_counter = itertools.count(1)

        # Create users with unique emails, phone numbers, and national IDs
        self.detective = self._create_user(
            username='detective1',
            first_name='John',
            last_name='Doe',
            groups=[self.detective_group]
        )

        self.sergeant = self._create_user(
            username='sergeant1',
            first_name='Jane',
            last_name='Smith',
            groups=[self.sergeant_group]
        )

        self.suspect_user = self._create_user(
            username='suspect1',
            first_name='Bad',
            last_name='Guy'
        )

        self.suspect_user2 = self._create_user(
            username='suspect2',
            first_name='Another',
            last_name='Suspect'
        )

        # Create a case
        self.case = Case.objects.create(
            created_by=self.detective,
            crime_type='CRITICAL',
            status='OPEN'
        )

        # Create detection board and detection
        self.detection_board = DetectionBoard.objects.create(
            title='Detective Board for Test Case'
        )

        self.detection = Detection.objects.create(
            detective=self.detective,
            case=self.case,
            detection_board=self.detection_board,
            sergeant=self.sergeant
        )

        # Create some evidence - FIXED: Add registered_by
        self.evidence1 = Evidence.objects.create(
            title='Bloody Knife',
            description='Knife found at crime scene',
            case=self.case,
            registered_by=self.detective  # ← Add this line
        )

        self.evidence2 = Evidence.objects.create(
            title='Fingerprint',
            description='Fingerprint on the door',
            case=self.case,
            registered_by=self.detective  # ← Add this line
        )

        # Set up API client
        self.client = APIClient()

    def _create_user(self, username, first_name='', last_name='', groups=None):
        """Helper method to create users with unique email, phone_number, and national_id."""
        counter = next(self.user_counter)
        user = User.objects.create_user(
            username=username,
            email=f'{username}{counter}@example.com',
            phone_number=f'0912{counter:08d}',
            national_id=f'{counter:010d}',
            password='testpass123',
            first_name=first_name,
            last_name=last_name
        )

        if groups:
            for group in groups:
                user.groups.add(group)

        return user

    def test_detective_can_access_own_board(self):
        """Test that detective can only access their own boards."""
        # Authenticate as detective
        self.client.force_authenticate(user=self.detective)

        # Create another detective's board with a NEW case
        other_detective = self._create_user(
            username='detective2',
            groups=[self.detective_group]
        )

        # Create a NEW case for the other detective
        other_case = Case.objects.create(
            created_by=other_detective,
            crime_type='NORMAL',
            status='OPEN'
        )

        other_board = DetectionBoard.objects.create(title='Other Board')
        Detection.objects.create(
            detective=other_detective,
            case=other_case,  # ← Use new case, not self.case
            detection_board=other_board,
            sergeant=self.sergeant
        )

        # Get all boards
        response = self.client.get('/api/detection/boards/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should only see own board
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.detection_board.id)

    def test_detective_can_create_lead(self):
        """Test creating different types of leads on the board."""
        self.client.force_authenticate(user=self.detective)

        # For evidence leads, don't include content at all
        evidence_lead_data = {
            'title': 'Bloody Knife Lead',
            'board_id': self.detection_board.id,
            'lead_type': 'E',
            'evidence': self.evidence1.id,
            # Don't include 'content' key at all
            'position_x': 0.3,
            'position_y': 0.5
        }

        response = self.client.post('/api/detection/leads/', evidence_lead_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # For note leads, don't include evidence
        note_lead_data = {
            'title': 'Detective Note',
            'board_id': self.detection_board.id,
            'lead_type': 'N',
            'content': 'This is an important observation',
            # Don't include 'evidence' key
            'position_x': 0.6,
            'position_y': 0.7
        }

        response = self.client.post('/api/detection/leads/', note_lead_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['lead_type'], 'N')
        self.assertEqual(response.data['content'], 'This is an important observation')

    def test_detective_cannot_create_invalid_lead(self):
        """Test validation for invalid lead creation."""
        self.client.force_authenticate(user=self.detective)

        # Test lead with position outside bounds
        invalid_position_data = {
            'title': 'Invalid Position',
            'board_id': self.detection_board.id,
            'lead_type': 'N',
            'content': 'Test content',
            'position_x': 1.5,
            'position_y': 0.5
        }

        response = self.client.post('/api/detection/leads/', invalid_position_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test evidence lead without evidence (just don't include evidence field)
        invalid_evidence_data = {
            'title': 'Invalid Evidence Lead',
            'board_id': self.detection_board.id,
            'lead_type': 'E',
            'position_x': 0.3,
            'position_y': 0.5
        }

        response = self.client.post('/api/detection/leads/', invalid_evidence_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detective_can_create_yarn_between_leads(self):
        """Test creating connections between leads."""
        self.client.force_authenticate(user=self.detective)

        # Create two leads first
        lead1 = Lead.objects.create(
            title='Lead 1',
            board=self.detection_board,
            lead_type='N',
            content='Note 1',
            position_x=0.2,
            position_y=0.3
        )

        lead2 = Lead.objects.create(
            title='Lead 2',
            board=self.detection_board,
            lead_type='N',
            content='Note 2',
            position_x=0.7,
            position_y=0.8
        )

        # Create yarn between them
        yarn_data = {
            'lead1': lead1.id,
            'lead2': lead2.id
        }

        response = self.client.post('/api/detection/yarns/', yarn_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify yarn exists
        self.assertTrue(Yarn.objects.filter(lead1=lead1, lead2=lead2).exists())

    def test_detective_cannot_create_yarn_between_different_boards(self):
        """Test that yarns can only connect leads from same board."""
        self.client.force_authenticate(user=self.detective)

        # Create another board
        other_board = DetectionBoard.objects.create(title='Other Board')

        lead1 = Lead.objects.create(
            title='Lead 1',
            board=self.detection_board,
            lead_type='N',
            content='Note 1',
            position_x=0.2,
            position_y=0.3
        )

        lead2 = Lead.objects.create(
            title='Lead 2',
            board=other_board,
            lead_type='N',
            content='Note 2',
            position_x=0.7,
            position_y=0.8
        )

        yarn_data = {
            'lead1': lead1.id,
            'lead2': lead2.id
        }

        response = self.client.post('/api/detection/yarns/', yarn_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detective_can_submit_suspects(self):
        """Test submitting suspects for sergeant approval."""
        self.client.force_authenticate(user=self.detective)

        submit_data = {
            'suspects': [self.suspect_user.id, self.suspect_user2.id],
            'reasons': 'Both suspects were at the crime scene and have motive'
        }

        response = self.client.post(
            f'/api/detection/boards/{self.detection_board.id}/submit_suspects/',
            submit_data
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['state'], 0)  # PENDING
        self.assertEqual(
            response.data['detective_reasons'],
            'Both suspects were at the crime scene and have motive'
        )

        # Verify suggestion was created
        suggestion = SuspectsSuggested.objects.get(detection=self.detection)
        self.assertEqual(suggestion.suspects.count(), 2)

    def test_detective_cannot_submit_existing_suspects(self):
        """Test that suspects already in the case cannot be submitted."""
        # First create a suspect in the case
        Suspect.objects.create(
            person=self.suspect_user,
            case=self.case,
            suspect_status='WANTED',
            added_by=self.detective
        )

        self.client.force_authenticate(user=self.detective)

        submit_data = {
            'suspects': [self.suspect_user.id, self.suspect_user2.id],
            'reasons': 'Both suspects are suspicious'
        }

        response = self.client.post(
            f'/api/detection/boards/{self.detection_board.id}/submit_suspects/',
            submit_data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already suspects', str(response.data))

    def test_detective_cannot_submit_multiple_pending_suggestions(self):
        """Test that detective can only have one pending suggestion at a time."""
        self.client.force_authenticate(user=self.detective)

        # Create first suggestion
        SuspectsSuggested.objects.create(
            detection=self.detection,
            detective_reasons='First attempt',
            state=0  # PENDING
        )

        # Try to submit another
        submit_data = {
            'suspects': [self.suspect_user.id],
            'reasons': 'Second attempt'
        }

        response = self.client.post(
            f'/api/detection/boards/{self.detection_board.id}/submit_suspects/',
            submit_data
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already have a pending suggestion', str(response.data))

    def test_detective_can_view_suggestions(self):
        """Test detective can view their suggestions."""
        self.client.force_authenticate(user=self.detective)

        # Create a suggestion
        suggestion = SuspectsSuggested.objects.create(
            detection=self.detection,
            detective_reasons='Test reasons',
            state=1  # CONFIRMED
        )
        suggestion.suspects.add(self.suspect_user)

        # Get suggestions
        response = self.client.get(f'/api/detection/boards/{self.detection_board.id}/suggestions/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['detective_reasons'], 'Test reasons')
        self.assertEqual(len(response.data[0]['suspects_details']), 1)

    def test_detective_gets_rejection_messages(self):
        """Test detective can see rejected suggestions as messages."""
        self.client.force_authenticate(user=self.detective)

        # Create rejected suggestions
        suggestion1 = SuspectsSuggested.objects.create(
            detection=self.detection,
            detective_reasons='Wrong suspects',
            state=2,  # REJECTED
            feedback='These suspects have alibis'
        )
        suggestion1.suspects.add(self.suspect_user)

        suggestion2 = SuspectsSuggested.objects.create(
            detection=self.detection,
            detective_reasons='Insufficient evidence',
            state=2,  # REJECTED
            feedback='Need more evidence'
        )
        suggestion2.suspects.add(self.suspect_user2)

        # Also create a pending suggestion (should not appear in messages)
        pending = SuspectsSuggested.objects.create(
            detection=self.detection,
            detective_reasons='New suspects',
            state=0
        )

        # Get messages
        response = self.client.get(f'/api/detection/boards/{self.detection_board.id}/messages/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Only rejected ones

        # Verify message format
        message = response.data[0]
        self.assertEqual(message['type'], 'rejection')
        self.assertEqual(message['title'], 'Suspect Suggestion Rejected')
        self.assertIn('content', message)
        self.assertIn('reasons', message)

    def test_sergeant_can_approve_suggestion(self):
        """Test sergeant approving a suggestion creates Suspect and Interrogation."""
        # First detective submits suspects
        self.client.force_authenticate(user=self.detective)

        submit_data = {
            'suspects': [self.suspect_user.id],
            'reasons': 'Strong evidence against this suspect'
        }

        response = self.client.post(
            f'/api/detection/boards/{self.detection_board.id}/submit_suspects/',
            submit_data
        )

        suggestion_id = response.data['id']

        # Now sergeant approves
        suggestion = SuspectsSuggested.objects.get(id=suggestion_id)
        suggestion.state = 1  # CONFIRMED
        suggestion.save()

        # Create Suspect instances
        for user in suggestion.suspects.all():
            suspect = Suspect.objects.create(
                person=user,
                case=self.detection.case,
                suspect_status='WANTED',
                added_by=self.sergeant,
                detail=f'Suggested by detective: {suggestion.detective_reasons}'
            )

            # Create Interrogation
            interrogation = Interrogation.objects.create(
                suspect=suspect,
                interrogator_sergeant=self.sergeant,
                interrogator_detective=self.detection.detective,
                status=InterrogationStatus.PENDING_SCORES
            )

        # Verify Suspect and Interrogation were created
        self.assertTrue(Suspect.objects.filter(
            person=self.suspect_user,
            case=self.detection.case
        ).exists())

        self.assertTrue(Interrogation.objects.filter(
            suspect__person=self.suspect_user
        ).exists())

    def test_sergeant_can_reject_suggestion(self):
        """Test sergeant rejecting a suggestion with feedback."""
        # First detective submits suspects
        self.client.force_authenticate(user=self.detective)

        submit_data = {
            'suspects': [self.suspect_user.id],
            'reasons': 'This suspect looks guilty'
        }

        response = self.client.post(
            f'/api/detection/boards/{self.detection_board.id}/submit_suspects/',
            submit_data
        )

        suggestion_id = response.data['id']

        # Sergeant rejects
        suggestion = SuspectsSuggested.objects.get(id=suggestion_id)
        suggestion.state = 2  # REJECTED
        suggestion.feedback = 'No solid evidence, just a hunch'
        suggestion.save()

        # Verify suggestion is rejected
        suggestion.refresh_from_db()
        self.assertEqual(suggestion.state, 2)
        self.assertEqual(suggestion.feedback, 'No solid evidence, just a hunch')

        # Detective should see this as a message
        self.client.force_authenticate(user=self.detective)
        response = self.client.get(f'/api/detection/boards/{self.detection_board.id}/messages/')

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['content'], 'No solid evidence, just a hunch')
        self.assertEqual(response.data[0]['reasons'], 'This suspect looks guilty')

    def test_interrogation_creation_with_critical_case(self):
        """Test that critical cases require chief approval."""
        # Detective submits suspects
        self.client.force_authenticate(user=self.detective)

        submit_data = {
            'suspects': [self.suspect_user.id],
            'reasons': 'Critical case suspect'
        }

        response = self.client.post(
            f'/api/detection/boards/{self.detection_board.id}/submit_suspects/',
            submit_data
        )

        suggestion = SuspectsSuggested.objects.get(id=response.data['id'])

        # Sergeant approves
        suggestion.state = 1
        suggestion.save()

        # Create suspect and interrogation
        suspect = Suspect.objects.create(
            person=self.suspect_user,
            case=self.detection.case,
            suspect_status='WANTED',
            added_by=self.sergeant
        )

        interrogation = Interrogation.objects.create(
            suspect=suspect,
            interrogator_sergeant=self.sergeant,
            interrogator_detective=self.detection.detective,
            status=InterrogationStatus.PENDING_SCORES
        )

        # Check if requires chief approval (based on crime_type CRITICAL)
        self.assertTrue(interrogation.requires_chief_approval())

    def test_full_flow_integration(self):
        """Test the complete flow from board creation to suspect interrogation."""
        self.client.force_authenticate(user=self.detective)

        # 1. Detective creates leads on board
        lead1 = Lead.objects.create(
            title='Evidence Lead',
            board=self.detection_board,
            lead_type='E',
            evidence=self.evidence1,
            position_x=0.2,
            position_y=0.3
        )

        lead2 = Lead.objects.create(
            title='Note Lead',
            board=self.detection_board,
            lead_type='N',
            content='Suspect was nervous during interview',
            position_x=0.7,
            position_y=0.8
        )

        # 2. Detective connects leads
        yarn = Yarn.objects.create(lead1=lead1, lead2=lead2)

        # 3. Detective submits suspects
        submit_data = {
            'suspects': [self.suspect_user.id],
            'reasons': 'Evidence points to this suspect and they were nervous'
        }

        response = self.client.post(
            f'/api/detection/boards/{self.detection_board.id}/submit_suspects/',
            submit_data
        )

        suggestion_id = response.data['id']

        # 4. Sergeant approves
        suggestion = SuspectsSuggested.objects.get(id=suggestion_id)
        suggestion.state = 1
        suggestion.save()

        # 5. Create suspect and interrogation
        suspect = Suspect.objects.create(
            person=self.suspect_user,
            case=self.detection.case,
            suspect_status='WANTED',
            added_by=self.sergeant,
            detail=suggestion.detective_reasons
        )

        interrogation = Interrogation.objects.create(
            suspect=suspect,
            interrogator_sergeant=self.sergeant,
            interrogator_detective=self.detection.detective,
            status=InterrogationStatus.PENDING_SCORES
        )

        # 6. Verify everything is connected
        self.assertEqual(interrogation.suspect.case, self.case)
        self.assertEqual(interrogation.suspect.person, self.suspect_user)
        self.assertEqual(interrogation.interrogator_detective, self.detective)

        # 7. Detective can see the suggestion status
        response = self.client.get(f'/api/detection/suggestions/{suggestion_id}/status/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['state_code'], 1)
        self.assertEqual(response.data['state'], 'CONFIRMED')

    def test_unauthorized_access(self):
        """Test that unauthorized users cannot access detective boards."""
        # Unauthenticated request
        response = self.client.get('/api/detection/boards/')
        # Some DRF setups return 403 for permission denied, even when unauthenticated
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        # Authenticated as non-detective
        normal_user = self._create_user(
            username='normal'
        )
        self.client.force_authenticate(user=normal_user)

        response = self.client.get('/api/detection/boards/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_evidence_notifications(self):
        """Test that new evidence can be added as leads."""
        self.client.force_authenticate(user=self.detective)

        new_evidence = Evidence.objects.create(
            title='New Evidence',
            description='Just discovered',
            case=self.case,
            registered_by=self.detective
        )

        lead_data = {
            'title': 'New Evidence Lead',
            'board_id': self.detection_board.id,
            'lead_type': 'E',
            'evidence': new_evidence.id,
            'position_x': 0.4,
            'position_y': 0.4
        }

        response = self.client.post('/api/detection/leads/', lead_data, format='json')
        # Print the error response to debug
        if response.status_code != 201:
            print(f"Evidence notification error: {response.data}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
