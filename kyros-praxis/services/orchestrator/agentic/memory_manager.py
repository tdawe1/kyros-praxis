"""
Persistent Memory and Context Management System

This module implements sophisticated memory management capabilities for agents,
providing persistent storage and retrieval of experiences, learned patterns,
and contextual information across sessions and runs.

The memory system supports:
- Episodic memory: Specific experiences and events
- Semantic memory: General knowledge and facts
- Procedural memory: Skills and procedures
- Working memory: Temporary context during execution
- Associative retrieval: Finding related memories
- Memory consolidation: Strengthening important memories
- Memory forgetting: Graceful degradation of old memories
"""

import asyncio
import json
import logging
import math
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_, desc
from pydantic import BaseModel, Field

from .models import AgentInstance, AgentMemory, AgentRun
try:
    from app.core.logging import log_orchestrator_event
except ImportError:
    def log_orchestrator_event(**kwargs):
        pass

logger = logging.getLogger(__name__)


class MemoryType(str, Enum):
    """Types of memory for categorization."""
    EPISODIC = "episodic"          # Specific experiences and events
    SEMANTIC = "semantic"          # General knowledge and facts  
    PROCEDURAL = "procedural"      # Skills and procedures
    WORKING = "working"            # Temporary context during execution
    META = "meta"                  # Meta-knowledge about learning


class MemoryImportance(str, Enum):
    """Importance levels for memory prioritization."""
    CRITICAL = "critical"          # Essential memories that should never be forgotten
    HIGH = "high"                  # Important memories for performance
    MEDIUM = "medium"              # Useful memories
    LOW = "low"                    # Background memories
    TEMPORARY = "temporary"        # Short-term memories


class MemoryStatus(str, Enum):
    """Memory lifecycle status."""
    ACTIVE = "active"              # Actively used memory
    DORMANT = "dormant"            # Inactive but retained memory
    CONSOLIDATING = "consolidating" # Being strengthened/refined
    DECAYING = "decaying"          # Gradually being forgotten
    ARCHIVED = "archived"          # Long-term storage


class MemoryQuery(BaseModel):
    """Query parameters for memory retrieval."""
    keywords: Optional[List[str]] = Field(default_factory=list)
    tags: Optional[List[str]] = Field(default_factory=list)
    memory_types: Optional[List[MemoryType]] = Field(default_factory=list)
    importance_min: Optional[MemoryImportance] = None
    time_range: Optional[Tuple[datetime, datetime]] = None
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_results: int = Field(default=20, ge=1, le=100)
    include_dormant: bool = Field(default=False)


class MemoryEntry(BaseModel):
    """Structured memory entry for storage."""
    content: str = Field(min_length=1)
    memory_type: MemoryType
    category: Optional[str] = None
    importance: MemoryImportance = Field(default=MemoryImportance.MEDIUM)
    tags: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    related_memory_ids: List[str] = Field(default_factory=list)
    source_run_id: Optional[str] = None
    expiry_date: Optional[datetime] = None


class MemoryCluster(BaseModel):
    """Cluster of related memories."""
    cluster_id: str
    theme: str
    memories: List[str]  # Memory IDs
    confidence: float
    created_at: datetime
    last_accessed: datetime


class MemoryManager:
    """
    Advanced memory management system for persistent agent memory.
    
    Manages storage, retrieval, and maintenance of agent memories with
    sophisticated features for associative retrieval, consolidation,
    and intelligent forgetting.
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.importance_weights = {
            MemoryImportance.CRITICAL: 1.0,
            MemoryImportance.HIGH: 0.8,
            MemoryImportance.MEDIUM: 0.6,
            MemoryImportance.LOW: 0.4,
            MemoryImportance.TEMPORARY: 0.2
        }
        self.decay_rates = {
            MemoryImportance.CRITICAL: 0.0,      # Never decay
            MemoryImportance.HIGH: 0.01,         # Very slow decay
            MemoryImportance.MEDIUM: 0.05,       # Moderate decay
            MemoryImportance.LOW: 0.1,           # Faster decay
            MemoryImportance.TEMPORARY: 0.3      # Rapid decay
        }
        
    async def store_memory(
        self,
        agent_instance_id: str,
        memory_entry: MemoryEntry
    ) -> str:
        """
        Store a new memory for an agent.
        
        Args:
            agent_instance_id: Agent to store memory for
            memory_entry: Memory data to store
            
        Returns:
            str: Memory ID
        """
        try:
            # Check if agent exists
            agent_result = await self.db.execute(
                select(AgentInstance).where(AgentInstance.id == agent_instance_id)
            )
            agent = agent_result.scalar_one_or_none()
            if not agent:
                raise ValueError(f"Agent instance {agent_instance_id} not found")
                
            # Create memory record
            memory = AgentMemory(
                agent_instance_id=agent_instance_id,
                memory_type=memory_entry.memory_type.value,
                category=memory_entry.category,
                importance=self.importance_weights[memory_entry.importance],
                content=memory_entry.content,
                structured_data={
                    'tags': memory_entry.tags,
                    'keywords': memory_entry.keywords,
                    'context': memory_entry.context,
                    'related_memory_ids': memory_entry.related_memory_ids,
                    'original_importance': memory_entry.importance.value
                },
                context=memory_entry.context,
                related_memories=memory_entry.related_memory_ids,
                tags=memory_entry.tags,
                keywords=memory_entry.keywords,
                confidence_score=memory_entry.confidence,
                source_run_id=memory_entry.source_run_id,
                expiry_date=memory_entry.expiry_date,
                last_accessed=datetime.utcnow(),
                last_updated=datetime.utcnow()
            )
            
            self.db.add(memory)
            await self.db.commit()
            await self.db.refresh(memory)
            
            # Update associations with related memories
            if memory_entry.related_memory_ids:
                await self._update_memory_associations(memory.id, memory_entry.related_memory_ids)
                
            log_orchestrator_event(
                event="memory_stored",
                agent_id=agent_instance_id,
                memory_id=memory.id,
                memory_type=memory_entry.memory_type.value,
                importance=memory_entry.importance.value,
                category=memory_entry.category
            )
            
            return memory.id
            
        except Exception as e:
            logger.error(f"Error storing memory: {e}", exc_info=True)
            raise
            
    async def retrieve_memories(
        self,
        agent_instance_id: str,
        query: MemoryQuery
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories matching query criteria.
        
        Args:
            agent_instance_id: Agent to retrieve memories for
            query: Query parameters
            
        Returns:
            List of matching memories
        """
        try:
            # Build base query
            base_query = select(AgentMemory).where(
                AgentMemory.agent_instance_id == agent_instance_id
            )
            
            # Add filters
            conditions = []
            
            # Memory type filter
            if query.memory_types:
                type_values = [mt.value for mt in query.memory_types]
                conditions.append(AgentMemory.memory_type.in_(type_values))
                
            # Importance filter
            if query.importance_min:
                min_importance = self.importance_weights[query.importance_min]
                conditions.append(AgentMemory.importance >= min_importance)
                
            # Time range filter
            if query.time_range:
                start_time, end_time = query.time_range
                conditions.append(
                    and_(
                        AgentMemory.created_at >= start_time,
                        AgentMemory.created_at <= end_time
                    )
                )
                
            # Status filter
            if not query.include_dormant:
                conditions.append(AgentMemory.archived == False)
                
            # Keyword search
            if query.keywords:
                keyword_conditions = []
                for keyword in query.keywords:
                    keyword_conditions.extend([
                        AgentMemory.content.contains(keyword),
                        AgentMemory.keywords.contains([keyword])
                    ])
                if keyword_conditions:
                    conditions.append(or_(*keyword_conditions))
                    
            # Tag search
            if query.tags:
                tag_conditions = []
                for tag in query.tags:
                    tag_conditions.append(AgentMemory.tags.contains([tag]))
                if tag_conditions:
                    conditions.append(or_(*tag_conditions))
                    
            # Apply all conditions
            if conditions:
                base_query = base_query.where(and_(*conditions))
                
            # Order by relevance (importance + recency + access frequency)
            base_query = base_query.order_by(
                desc(AgentMemory.importance),
                desc(AgentMemory.access_count),
                desc(AgentMemory.created_at)
            ).limit(query.max_results)
            
            # Execute query
            result = await self.db.execute(base_query)
            memories = result.scalars().all()
            
            # Update access counts
            memory_ids = [m.id for m in memories]
            if memory_ids:
                await self._update_access_counts(memory_ids)
                
            # Convert to return format
            memory_list = []
            for memory in memories:
                memory_dict = {
                    'id': memory.id,
                    'content': memory.content,
                    'memory_type': memory.memory_type,
                    'category': memory.category,
                    'importance': memory.importance,
                    'tags': memory.tags or [],
                    'keywords': memory.keywords or [],
                    'context': memory.context or {},
                    'confidence_score': memory.confidence_score,
                    'access_count': memory.access_count,
                    'created_at': memory.created_at.isoformat(),
                    'last_accessed': memory.last_accessed.isoformat() if memory.last_accessed else None,
                    'related_memories': memory.related_memories or []
                }
                memory_list.append(memory_dict)
                
            log_orchestrator_event(
                event="memories_retrieved",
                agent_id=agent_instance_id,
                query_params={
                    'keywords': query.keywords,
                    'tags': query.tags,
                    'memory_types': [mt.value for mt in query.memory_types] if query.memory_types else []
                },
                results_count=len(memory_list)
            )
            
            return memory_list
            
        except Exception as e:
            logger.error(f"Error retrieving memories: {e}", exc_info=True)
            return []
            
    async def find_similar_memories(
        self,
        agent_instance_id: str,
        reference_content: str,
        max_results: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find memories similar to reference content using semantic similarity.
        
        Args:
            agent_instance_id: Agent to search memories for
            reference_content: Content to find similar memories for
            max_results: Maximum number of results
            threshold: Similarity threshold
            
        Returns:
            List of similar memories with similarity scores
        """
        try:
            # Get all memories for the agent
            all_memories_result = await self.db.execute(
                select(AgentMemory)
                .where(AgentMemory.agent_instance_id == agent_instance_id)
                .where(AgentMemory.archived == False)
            )
            all_memories = all_memories_result.scalars().all()
            
            if not all_memories:
                return []
                
            # Calculate similarity scores (simplified implementation)
            # In production, this would use proper semantic similarity (embeddings)
            similar_memories = []
            
            reference_words = set(reference_content.lower().split())
            
            for memory in all_memories:
                memory_words = set(memory.content.lower().split())
                
                # Simple Jaccard similarity
                intersection = len(reference_words & memory_words)
                union = len(reference_words | memory_words)
                similarity = intersection / union if union > 0 else 0.0
                
                # Boost similarity for keyword matches
                keyword_boost = 0.0
                if memory.keywords:
                    keyword_matches = sum(1 for keyword in memory.keywords 
                                        if keyword.lower() in reference_content.lower())
                    keyword_boost = (keyword_matches / len(memory.keywords)) * 0.3
                    
                # Boost similarity for tag matches
                tag_boost = 0.0
                if memory.tags:
                    reference_words_set = set(reference_content.lower().split())
                    tag_matches = sum(1 for tag in memory.tags 
                                    if tag.lower() in reference_words_set)
                    tag_boost = (tag_matches / len(memory.tags)) * 0.2
                    
                final_similarity = min(similarity + keyword_boost + tag_boost, 1.0)
                
                if final_similarity >= threshold:
                    similar_memories.append({
                        'memory': memory,
                        'similarity': final_similarity
                    })
                    
            # Sort by similarity and limit results
            similar_memories.sort(key=lambda x: x['similarity'], reverse=True)
            similar_memories = similar_memories[:max_results]
            
            # Update access counts
            memory_ids = [sm['memory'].id for sm in similar_memories]
            if memory_ids:
                await self._update_access_counts(memory_ids)
                
            # Format results
            results = []
            for item in similar_memories:
                memory = item['memory']
                results.append({
                    'id': memory.id,
                    'content': memory.content,
                    'memory_type': memory.memory_type,
                    'category': memory.category,
                    'importance': memory.importance,
                    'similarity_score': item['similarity'],
                    'tags': memory.tags or [],
                    'keywords': memory.keywords or [],
                    'created_at': memory.created_at.isoformat(),
                    'access_count': memory.access_count
                })
                
            log_orchestrator_event(
                event="similar_memories_found",
                agent_id=agent_instance_id,
                reference_content=reference_content[:100],
                results_count=len(results),
                avg_similarity=sum(r['similarity_score'] for r in results) / len(results) if results else 0
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar memories: {e}", exc_info=True)
            return []
            
    async def consolidate_memories(
        self,
        agent_instance_id: str,
        consolidation_threshold: int = 50
    ) -> Dict[str, Any]:
        """
        Consolidate and strengthen important memories.
        
        Args:
            agent_instance_id: Agent to consolidate memories for
            consolidation_threshold: Minimum access count for consolidation
            
        Returns:
            Dict with consolidation results
        """
        try:
            # Find frequently accessed memories
            frequent_memories_result = await self.db.execute(
                select(AgentMemory)
                .where(AgentMemory.agent_instance_id == agent_instance_id)
                .where(AgentMemory.access_count >= consolidation_threshold)
                .where(AgentMemory.archived == False)
            )
            frequent_memories = frequent_memories_result.scalars().all()
            
            consolidation_actions = {
                'memories_consolidated': 0,
                'importance_increased': 0,
                'clusters_created': 0,
                'associations_strengthened': 0
            }
            
            for memory in frequent_memories:
                # Increase importance for frequently accessed memories
                if memory.importance < 0.9:  # Don't exceed max importance
                    old_importance = memory.importance
                    memory.importance = min(memory.importance + 0.1, 1.0)
                    
                    if memory.importance > old_importance:
                        consolidation_actions['importance_increased'] += 1
                        
                    await self.db.commit()
                    
                consolidation_actions['memories_consolidated'] += 1
                
            # Find and create memory clusters
            clusters = await self._identify_memory_clusters(agent_instance_id)
            consolidation_actions['clusters_created'] = len(clusters)
            
            # Strengthen associations between related memories
            associations_strengthened = await self._strengthen_associations(agent_instance_id)
            consolidation_actions['associations_strengthened'] = associations_strengthened
            
            log_orchestrator_event(
                event="memory_consolidation_completed",
                agent_id=agent_instance_id,
                **consolidation_actions
            )
            
            return consolidation_actions
            
        except Exception as e:
            logger.error(f"Error consolidating memories: {e}", exc_info=True)
            return {'error': str(e)}
            
    async def forget_memories(
        self,
        agent_instance_id: str,
        max_memories: int = 1000,
        preserve_critical: bool = True
    ) -> Dict[str, Any]:
        """
        Implement graceful memory forgetting to manage memory size.
        
        Args:
            agent_instance_id: Agent to forget memories for
            max_memories: Maximum number of memories to keep
            preserve_critical: Whether to preserve critical memories
            
        Returns:
            Dict with forgetting results
        """
        try:
            # Count current memories
            total_count_result = await self.db.execute(
                select(func.count(AgentMemory.id))
                .where(AgentMemory.agent_instance_id == agent_instance_id)
                .where(AgentMemory.archived == False)
            )
            total_count = total_count_result.scalar()
            
            if total_count <= max_memories:
                return {'memories_forgotten': 0, 'memories_archived': 0, 'total_remaining': total_count}
                
            # Calculate how many memories to remove
            memories_to_remove = total_count - max_memories
            
            # Build forgetting criteria (preserve important and recent memories)
            forgetting_query = select(AgentMemory).where(
                AgentMemory.agent_instance_id == agent_instance_id,
                AgentMemory.archived == False
            )
            
            if preserve_critical:
                # Don't forget critical memories
                forgetting_query = forgetting_query.where(
                    AgentMemory.importance < self.importance_weights[MemoryImportance.CRITICAL]
                )
                
            # Order by forgetting priority (low importance, old, infrequently accessed)
            forgetting_query = forgetting_query.order_by(
                AgentMemory.importance.asc(),
                AgentMemory.access_count.asc(),
                AgentMemory.created_at.asc()
            ).limit(memories_to_remove)
            
            result = await self.db.execute(forgetting_query)
            memories_to_forget = result.scalars().all()
            
            # Archive instead of deleting (graceful forgetting)
            memories_forgotten = 0
            memories_archived = 0
            
            for memory in memories_to_forget:
                if memory.importance <= self.importance_weights[MemoryImportance.LOW]:
                    # Actually delete very unimportant memories
                    await self.db.delete(memory)
                    memories_forgotten += 1
                else:
                    # Archive moderately important memories
                    memory.archived = True
                    memories_archived += 1
                    
            await self.db.commit()
            
            # Update final count
            final_count_result = await self.db.execute(
                select(func.count(AgentMemory.id))
                .where(AgentMemory.agent_instance_id == agent_instance_id)
                .where(AgentMemory.archived == False)
            )
            final_count = final_count_result.scalar()
            
            forgetting_results = {
                'memories_forgotten': memories_forgotten,
                'memories_archived': memories_archived,
                'total_removed': memories_forgotten + memories_archived,
                'total_remaining': final_count
            }
            
            log_orchestrator_event(
                event="memory_forgetting_completed",
                agent_id=agent_instance_id,
                **forgetting_results
            )
            
            return forgetting_results
            
        except Exception as e:
            logger.error(f"Error in memory forgetting: {e}", exc_info=True)
            return {'error': str(e)}
            
    async def get_memory_statistics(
        self,
        agent_instance_id: str
    ) -> Dict[str, Any]:
        """
        Get comprehensive memory statistics for an agent.
        
        Args:
            agent_instance_id: Agent to get statistics for
            
        Returns:
            Dict with memory statistics
        """
        try:
            # Total memories
            total_result = await self.db.execute(
                select(func.count(AgentMemory.id))
                .where(AgentMemory.agent_instance_id == agent_instance_id)
                .where(AgentMemory.archived == False)
            )
            total_memories = total_result.scalar()
            
            # Memories by type
            type_stats = {}
            for memory_type in MemoryType:
                type_result = await self.db.execute(
                    select(func.count(AgentMemory.id))
                    .where(AgentMemory.agent_instance_id == agent_instance_id)
                    .where(AgentMemory.memory_type == memory_type.value)
                    .where(AgentMemory.archived == False)
                )
                type_stats[memory_type.value] = type_result.scalar()
                
            # Memories by importance level
            importance_stats = {}
            for importance in MemoryImportance:
                weight = self.importance_weights[importance]
                # Find memories within importance range
                if importance == MemoryImportance.CRITICAL:
                    importance_filter = AgentMemory.importance >= weight
                else:
                    # Get the next higher importance weight for range
                    importance_values = list(self.importance_weights.values())
                    importance_values.sort(reverse=True)
                    try:
                        next_weight = importance_values[importance_values.index(weight) - 1]
                        importance_filter = and_(
                            AgentMemory.importance >= weight,
                            AgentMemory.importance < next_weight
                        )
                    except (ValueError, IndexError):
                        importance_filter = AgentMemory.importance >= weight
                        
                importance_result = await self.db.execute(
                    select(func.count(AgentMemory.id))
                    .where(AgentMemory.agent_instance_id == agent_instance_id)
                    .where(importance_filter)
                    .where(AgentMemory.archived == False)
                )
                importance_stats[importance.value] = importance_result.scalar()
                
            # Recent memory activity
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_result = await self.db.execute(
                select(func.count(AgentMemory.id))
                .where(AgentMemory.agent_instance_id == agent_instance_id)
                .where(AgentMemory.created_at >= week_ago)
                .where(AgentMemory.archived == False)
            )
            recent_memories = recent_result.scalar()
            
            # Most accessed memories
            top_accessed_result = await self.db.execute(
                select(AgentMemory.content, AgentMemory.access_count)
                .where(AgentMemory.agent_instance_id == agent_instance_id)
                .where(AgentMemory.archived == False)
                .order_by(desc(AgentMemory.access_count))
                .limit(5)
            )
            top_accessed = [
                {'content': content[:100], 'access_count': count}
                for content, count in top_accessed_result.fetchall()
            ]
            
            # Memory age distribution
            age_stats = await self._calculate_memory_age_distribution(agent_instance_id)
            
            statistics = {
                'total_memories': total_memories,
                'memories_by_type': type_stats,
                'memories_by_importance': importance_stats,
                'recent_memories_week': recent_memories,
                'top_accessed_memories': top_accessed,
                'memory_age_distribution': age_stats,
                'average_access_count': await self._calculate_average_access_count(agent_instance_id),
                'memory_utilization': await self._calculate_memory_utilization(agent_instance_id)
            }
            
            return statistics
            
        except Exception as e:
            logger.error(f"Error getting memory statistics: {e}", exc_info=True)
            return {'error': str(e)}
            
    # Helper methods
    
    async def _update_memory_associations(self, memory_id: str, related_ids: List[str]):
        """Update bidirectional associations between memories."""
        for related_id in related_ids:
            # Get related memory
            related_result = await self.db.execute(
                select(AgentMemory).where(AgentMemory.id == related_id)
            )
            related_memory = related_result.scalar_one_or_none()
            
            if related_memory:
                # Add bidirectional association
                current_related = related_memory.related_memories or []
                if memory_id not in current_related:
                    current_related.append(memory_id)
                    related_memory.related_memories = current_related
                    await self.db.commit()
                    
    async def _update_access_counts(self, memory_ids: List[str]):
        """Update access counts for memories."""
        await self.db.execute(
            update(AgentMemory)
            .where(AgentMemory.id.in_(memory_ids))
            .values(
                access_count=AgentMemory.access_count + 1,
                last_accessed=datetime.utcnow()
            )
        )
        await self.db.commit()
        
    async def _identify_memory_clusters(self, agent_instance_id: str) -> List[MemoryCluster]:
        """Identify clusters of related memories."""
        # Simplified clustering implementation
        # In production, would use proper clustering algorithms
        clusters = []
        
        # Find memories with common tags
        memories_result = await self.db.execute(
            select(AgentMemory)
            .where(AgentMemory.agent_instance_id == agent_instance_id)
            .where(AgentMemory.archived == False)
            .where(AgentMemory.tags.isnot(None))
        )
        memories = memories_result.scalars().all()
        
        # Group by common tags
        tag_groups = {}
        for memory in memories:
            if memory.tags:
                for tag in memory.tags:
                    if tag not in tag_groups:
                        tag_groups[tag] = []
                    tag_groups[tag].append(memory.id)
                    
        # Create clusters for tags with multiple memories
        for tag, memory_ids in tag_groups.items():
            if len(memory_ids) >= 3:  # Minimum cluster size
                cluster = MemoryCluster(
                    cluster_id=str(uuid4()),
                    theme=tag,
                    memories=memory_ids,
                    confidence=0.8,
                    created_at=datetime.utcnow(),
                    last_accessed=datetime.utcnow()
                )
                clusters.append(cluster)
                
        return clusters
        
    async def _strengthen_associations(self, agent_instance_id: str) -> int:
        """Strengthen associations between frequently co-accessed memories."""
        # Simplified association strengthening
        # In production, would track co-access patterns
        associations_strengthened = 0
        
        # Find memories that are frequently accessed together
        # This is a placeholder implementation
        memories_result = await self.db.execute(
            select(AgentMemory)
            .where(AgentMemory.agent_instance_id == agent_instance_id)
            .where(AgentMemory.access_count > 10)
            .where(AgentMemory.archived == False)
        )
        frequent_memories = memories_result.scalars().all()
        
        # Create associations based on similar categories/tags
        for i, memory1 in enumerate(frequent_memories):
            for memory2 in frequent_memories[i+1:]:
                # Check for category or tag similarity
                should_associate = False
                
                if memory1.category and memory1.category == memory2.category:
                    should_associate = True
                elif memory1.tags and memory2.tags:
                    common_tags = set(memory1.tags) & set(memory2.tags)
                    if len(common_tags) >= 2:
                        should_associate = True
                        
                if should_associate:
                    # Add bidirectional association
                    related1 = memory1.related_memories or []
                    related2 = memory2.related_memories or []
                    
                    if memory2.id not in related1:
                        related1.append(memory2.id)
                        memory1.related_memories = related1
                        
                    if memory1.id not in related2:
                        related2.append(memory1.id)
                        memory2.related_memories = related2
                        
                    associations_strengthened += 1
                    
        await self.db.commit()
        return associations_strengthened
        
    async def _calculate_memory_age_distribution(self, agent_instance_id: str) -> Dict[str, int]:
        """Calculate distribution of memory ages."""
        now = datetime.utcnow()
        
        age_buckets = {
            'last_day': 0,
            'last_week': 0,
            'last_month': 0,
            'last_year': 0,
            'older': 0
        }
        
        memories_result = await self.db.execute(
            select(AgentMemory.created_at)
            .where(AgentMemory.agent_instance_id == agent_instance_id)
            .where(AgentMemory.archived == False)
        )
        
        for (created_at,) in memories_result.fetchall():
            age = now - created_at
            
            if age <= timedelta(days=1):
                age_buckets['last_day'] += 1
            elif age <= timedelta(days=7):
                age_buckets['last_week'] += 1
            elif age <= timedelta(days=30):
                age_buckets['last_month'] += 1
            elif age <= timedelta(days=365):
                age_buckets['last_year'] += 1
            else:
                age_buckets['older'] += 1
                
        return age_buckets
        
    async def _calculate_average_access_count(self, agent_instance_id: str) -> float:
        """Calculate average access count across all memories."""
        result = await self.db.execute(
            select(func.avg(AgentMemory.access_count))
            .where(AgentMemory.agent_instance_id == agent_instance_id)
            .where(AgentMemory.archived == False)
        )
        avg_access = result.scalar()
        return float(avg_access) if avg_access else 0.0
        
    async def _calculate_memory_utilization(self, agent_instance_id: str) -> Dict[str, float]:
        """Calculate memory utilization metrics."""
        # Total memories
        total_result = await self.db.execute(
            select(func.count(AgentMemory.id))
            .where(AgentMemory.agent_instance_id == agent_instance_id)
            .where(AgentMemory.archived == False)
        )
        total = total_result.scalar()
        
        if total == 0:
            return {'accessed_recently': 0.0, 'high_access': 0.0, 'high_importance': 0.0}
            
        # Recently accessed
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_result = await self.db.execute(
            select(func.count(AgentMemory.id))
            .where(AgentMemory.agent_instance_id == agent_instance_id)
            .where(AgentMemory.last_accessed >= week_ago)
            .where(AgentMemory.archived == False)
        )
        recent = recent_result.scalar()
        
        # High access count
        high_access_result = await self.db.execute(
            select(func.count(AgentMemory.id))
            .where(AgentMemory.agent_instance_id == agent_instance_id)
            .where(AgentMemory.access_count >= 10)
            .where(AgentMemory.archived == False)
        )
        high_access = high_access_result.scalar()
        
        # High importance
        high_importance_result = await self.db.execute(
            select(func.count(AgentMemory.id))
            .where(AgentMemory.agent_instance_id == agent_instance_id)
            .where(AgentMemory.importance >= self.importance_weights[MemoryImportance.HIGH])
            .where(AgentMemory.archived == False)
        )
        high_importance = high_importance_result.scalar()
        
        return {
            'accessed_recently': recent / total,
            'high_access': high_access / total,
            'high_importance': high_importance / total
        }