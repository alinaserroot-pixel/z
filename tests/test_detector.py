"""Tests for form field detection"""

import pytest
from app.browser.detector import FieldDetector, FormField


class TestFieldDetector:
    """Test field detection and scoring"""
    
    def setup_method(self):
        self.detector = FieldDetector()
    
    def test_email_field_detection(self):
        """Test email field detection"""
        field = FormField(
            selector="input[name='email']",
            field_type="email",
            name="email"
        )
        
        score = self.detector.score_field_match({
            "type": "email",
            "name": "email",
            "id": "",
            "placeholder": "",
            "label": "",
            "autocomplete": "email"
        }, "email")
        
        assert score > 40  # Should score high
    
    def test_password_field_detection(self):
        """Test password field detection"""
        score = self.detector.score_field_match({
            "type": "password",
            "name": "password",
            "id": "",
            "placeholder": "",
            "label": "",
            "autocomplete": "new-password"
        }, "password")
        
        assert score > 40
    
    def test_name_field_detection(self):
        """Test name field detection"""
        score = self.detector.score_field_match({
            "type": "text",
            "name": "full_name",
            "id": "",
            "placeholder": "Enter your full name",
            "label": "Full Name",
            "autocomplete": ""
        }, "full_name")
        
        assert score > 20
    
    def test_phone_field_detection(self):
        """Test phone field detection"""
        score = self.detector.score_field_match({
            "type": "tel",
            "name": "phone",
            "id": "phone_number",
            "placeholder": "+1 (555) 000-0000",
            "label": "Phone Number",
            "autocomplete": ""
        }, "phone")
        
        assert score > 20
    
    def test_placeholder_scoring(self):
        """Test that placeholder text contributes to scoring"""
        score1 = self.detector.score_field_match({
            "type": "text",
            "name": "username",
            "id": "",
            "placeholder": "john_doe",
            "label": "",
            "autocomplete": ""
        }, "username")
        
        score2 = self.detector.score_field_match({
            "type": "text",
            "name": "username",
            "id": "",
            "placeholder": "Enter text",
            "label": "",
            "autocomplete": ""
        }, "username")
        
        assert score1 > score2
    
    def test_find_best_field(self):
        """Test finding the best matching field"""
        fields = [
            FormField(selector="input[name='user']", field_type="text", name="user"),
            FormField(selector="input[name='email']", field_type="email", name="email"),
            FormField(selector="input[name='mail']", field_type="text", name="mail"),
        ]
        
        best = self.detector.find_best_field(fields, "email")
        assert best is not None
        assert best.name == "email"
        assert best.score > 0
