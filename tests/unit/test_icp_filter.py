import pytest
from packages.core.models.icp import ICPConfig


class TestICPFilter:
    """Test ICP filtering logic"""
    
    def test_company_size_filter(self, icp_config):
        """Test company size filtering based on ICP"""
        min_size, max_size = icp_config.size_range
        
        # Test companies within range
        assert min_size <= 100 <= max_size
        assert min_size <= 250 <= max_size
        
        # Test companies outside range
        assert not (min_size <= 10 <= max_size)  # Too small
        assert not (min_size <= 1000 <= max_size)  # Too large
    
    def test_arr_filter(self, icp_config):
        """Test ARR filtering based on ICP"""
        min_arr, max_arr = icp_config.arr_range
        
        # Test ARR within range
        assert min_arr <= 10_000_000 <= max_arr
        assert min_arr <= 25_000_000 <= max_arr
        
        # Test ARR outside range
        assert not (min_arr <= 1_000_000 <= max_arr)  # Too low
        assert not (min_arr <= 100_000_000 <= max_arr)  # Too high
    
    def test_tech_stack_filter(self, icp_config):
        """Test technology stack filtering"""
        target_tech = icp_config.tech_stack
        
        # Test matching technologies
        assert "HubSpot" in target_tech
        assert "Salesforce" in target_tech
        
        # Test technology matching
        company_tech_a = ["HubSpot", "Salesforce", "Slack"]
        company_tech_b = ["Excel", "Manual processes"]
        
        matches_a = any(tech in target_tech for tech in company_tech_a)
        matches_b = any(tech in target_tech for tech in company_tech_b)
        
        assert matches_a
        assert not matches_b
    
    def test_icp_score_calculation(self):
        """Test ICP score calculation"""
        # Simple scoring logic
        def calculate_icp_score(
            company_size: int,
            arr_usd: int,
            tech_match: bool
        ) -> int:
            score = 0
            
            # Size score (40 points max)
            if 50 <= company_size <= 500:
                score += 40
            
            # ARR score (40 points max)
            if 5_000_000 <= arr_usd <= 50_000_000:
                score += 40
            
            # Tech stack score (20 points max)
            if tech_match:
                score += 20
            
            return score
        
        # Test good ICP fit
        score_good = calculate_icp_score(200, 15_000_000, True)
        assert score_good == 100
        
        # Test partial ICP fit
        score_partial = calculate_icp_score(200, 15_000_000, False)
        assert score_partial == 80
        
        # Test poor ICP fit
        score_poor = calculate_icp_score(20, 1_000_000, False)
        assert score_poor == 0