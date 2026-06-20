import asyncio
from typing import Optional
from datetime import datetime
from ...packages.core.models.signal import Signal
from ...packages.core.models.lead import Lead
from ...packages.core.models.icp import ICPConfig
from ...packages.core.events import SignalDetected, LeadEnriched
from ...packages.integrations.tavily.signal_extractor import TavilySignalExtractor
from ...infra.firebase.firestore import FirestoreClient


class PassiveListener:
    """Orchestrates passive signal listening from multiple sources"""
    
    def __init__(
        self,
        icp_config: ICPConfig,
        signal_extractor: TavilySignalExtractor,
        firestore_client: Optional[FirestoreClient] = None,
        check_interval: int = 300  # 5 minutes
    ):
        self.icp_config = icp_config
        self.signal_extractor = signal_extractor
        self.firestore_client = firestore_client
        self.check_interval = check_interval
        self.running = False
    
    async def start(self):
        """Start the passive listener"""
        self.running = True
        print("🎯 Starting passive listener...")
        
        # Run signal detection loop
        while self.running:
            try:
                await self._detect_signals()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                print(f"❌ Error in signal detection: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def stop(self):
        """Stop the passive listener"""
        self.running = False
        print("🛑 Stopping passive listener...")
    
    async def _detect_signals(self):
        """Detect signals from all configured sources"""
        print(f"🔍 Scanning for signals at {datetime.utcnow().isoformat()}...")
        
        # Detect signals from Tavily
        tavily_signals = await self.signal_extractor.extract_signals()
        print(f"📡 Detected {len(tavily_signals)} signals from Tavily")
        
        # Process each signal
        for signal in tavily_signals:
            await self._process_signal(signal)
    
    async def _process_signal(self, signal: Signal):
        """Process a detected signal"""
        try:
            # Check for duplicates
            if self.firestore_client:
                is_duplicate = await self.firestore_client.check_duplicate_signal(
                    signal.company_name,
                    signal.raw_text
                )
                if is_duplicate:
                    print(f"⏭️  Skipping duplicate signal: {signal.company_name}")
                    return
            
            # Apply ICP pre-filter
            signal.icp_pre_score = self._calculate_icp_pre_score(signal)
            
            # Save signal to Firestore
            if self.firestore_client:
                await self.firestore_client.save_signal(signal)
            
            # Emit signal detected event
            event = SignalDetected(
                data={
                    "signal": signal.model_dump(),
                    "source": signal.source,
                    "icp_pre_score": signal.icp_pre_score
                }
            )
            await self._emit_event(event)
            
            print(f"✅ Processed signal: {signal.company_name} (score: {signal.icp_pre_score})")
            
            # If signal passes threshold, trigger enrichment
            if signal.icp_pre_score and signal.icp_pre_score >= 50:
                await self._trigger_enrichment(signal)
        
        except Exception as e:
            print(f"❌ Error processing signal: {e}")
    
    def _calculate_icp_pre_score(self, signal: Signal) -> float:
        """Calculate preliminary ICP score based on keywords"""
        base_score = 0.0
        
        # Score based on keyword matches
        for keyword in signal.keywords_hit:
            if keyword in ["RevOps", "Revenue Operations"]:
                base_score += 30
            elif keyword in ["Sales Engineer"]:
                base_score += 25
            elif keyword in ["HubSpot", "Salesforce"]:
                base_score += 10
            elif keyword in ["Series A", "Series B"]:
                base_score += 20
            elif keyword in ["pipeline", "attribution"]:
                base_score += 15
        
        # Source bonus
        if signal.source == "conference_audio":
            base_score += 5
        
        return min(base_score, 100.0)
    
    async def _trigger_enrichment(self, signal: Signal):
        """Trigger enrichment for high-scoring signals"""
        print(f"🔄 Triggering enrichment for {signal.company_name}...")
        
        # This would trigger the enrichment pipeline
        # For now, just log that enrichment would be triggered
        pass
    
    async def _emit_event(self, event):
        """Emit a domain event (would typically go to a message broker)"""
        print(f"📢 Emitting event: {event.event_type}")
        # In production, this would publish to GCP Pub/Sub
        # For now, just log the event