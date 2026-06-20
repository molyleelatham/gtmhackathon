from typing import Optional, Any
from datetime import datetime
from firebase_admin import firestore
from .admin import ensure_firebase_initialized
from ...packages.core.models.signal import Signal
from ...packages.core.models.lead import Lead


class FirestoreClient:
    """Firebase Firestore client for data persistence"""
    
    def __init__(self, service_account_key: Optional[str] = None):
        """
        Initialize Firebase Firestore client
        
        Args:
            service_account_key: Path to service account key JSON file or JSON string
        """
        ensure_firebase_initialized(service_account_key)
        self.db = firestore.client()
    
    async def save_signal(self, signal: Signal) -> str:
        """
        Save a signal to Firestore
        
        Args:
            signal: Signal object to save
        
        Returns:
            Document ID
        """
        doc_ref = self.db.collection("signals").document(signal.id)
        doc_ref.set(signal.model_dump())
        return signal.id
    
    async def get_signal(self, signal_id: str) -> Optional[dict[str, Any]]:
        """
        Get a signal by ID
        
        Args:
            signal_id: Signal document ID
        
        Returns:
            Signal data or None if not found
        """
        doc_ref = self.db.collection("signals").document(signal_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        return None
    
    async def save_lead(self, lead: Lead) -> str:
        """
        Save a lead to Firestore
        
        Args:
            lead: Lead object to save
        
        Returns:
            Document ID
        """
        doc_ref = self.db.collection("leads").document(lead.id)
        doc_ref.set(lead.model_dump())
        return lead.id
    
    async def get_lead(self, lead_id: str) -> Optional[dict[str, Any]]:
        """
        Get a lead by ID
        
        Args:
            lead_id: Lead document ID
        
        Returns:
            Lead data or None if not found
        """
        doc_ref = self.db.collection("leads").document(lead_id)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict()
        return None
    
    async def update_lead(self, lead_id: str, updates: dict[str, Any]) -> bool:
        """
        Update a lead in Firestore
        
        Args:
            lead_id: Lead document ID
            updates: Dictionary of fields to update
        
        Returns:
            True if successful, False otherwise
        """
        doc_ref = self.db.collection("leads").document(lead_id)
        doc_ref.update(updates)
        return True
    
    async def query_signals_by_company(
        self,
        company_name: str,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Query signals by company name
        
        Args:
            company_name: Company name to search for
            limit: Maximum number of results
        
        Returns:
            List of signal documents
        """
        signals_ref = self.db.collection("signals")
        query = signals_ref.where("company_name", "==", company_name).limit(limit)
        results = query.stream()
        
        return [doc.to_dict() for doc in results]
    
    async def query_leads_by_score(
        self,
        min_score: int,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Query leads by minimum ICP score
        
        Args:
            min_score: Minimum ICP score
            limit: Maximum number of results
        
        Returns:
            List of lead documents
        """
        leads_ref = self.db.collection("leads")
        query = leads_ref.where("icp_score", ">=", min_score).limit(limit)
        results = query.stream()
        
        return [doc.to_dict() for doc in results]
    
    async def check_duplicate_signal(
        self,
        company_name: str,
        raw_text: str,
        hours: int = 24
    ) -> bool:
        """
        Check if a similar signal already exists within the specified time window
        
        Args:
            company_name: Company name to check
            raw_text: Signal text to check for similarity
            hours: Time window in hours
        
        Returns:
            True if duplicate found, False otherwise
        """
        from datetime import timedelta
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        signals_ref = self.db.collection("signals")
        query = (
            signals_ref
            .where("company_name", "==", company_name)
            .where("detected_at", ">=", cutoff_time)
            .limit(5)
        )
        
        results = query.stream()
        
        for doc in results:
            signal_data = doc.to_dict()
            # Simple duplicate check: same company and similar text
            if raw_text == signal_data.get("raw_text", ""):
                return True
        
        return False