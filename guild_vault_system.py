"""
Guild Vault and Resource Pooling System for Age of Scribes
==========================================================

This module provides comprehensive vault management for guilds, including shared resource
pooling, member access controls, security mechanisms, and transaction auditing. The system
handles deposits, withdrawals, theft prevention, and integration with guild governance.

Key Features:
- Secure resource storage with configurable access policies
- Transaction logging and audit trails
- Security levels affecting theft and unauthorized access
- PC integration for legitimate and illicit vault interactions
- Integration with guild charter, reputation, and justice systems

Author: Age of Scribes Development Team
"""

import uuid
import random
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum

# Forward declarations for type checking
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from guild_event_engine import LocalGuild
    from npc_profile import NPCProfile


class AccessLevel(Enum):
    """Vault access permission levels."""
    NONE = "none"
    DEPOSIT = "deposit"
    WITHDRAW_LIMITED = "withdraw_limited"
    WITHDRAW = "withdraw"
    FULL_ACCESS = "full_access"
    EMERGENCY_ACCESS = "emergency_access"


class TransactionType(Enum):
    """Types of vault transactions."""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    THEFT = "theft"
    CONFISCATION = "confiscation"
    EMERGENCY_ACCESS = "emergency_access"
    AUDIT_ADJUSTMENT = "audit_adjustment"


class SecurityLevel(Enum):
    """Vault security configurations."""
    MINIMAL = "minimal"
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    MAXIMUM = "maximum"


class VaultAlert(Enum):
    """Types of vault security alerts."""
    SUSPICIOUS_WITHDRAWAL = "suspicious_withdrawal"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    LARGE_TRANSACTION = "large_transaction"
    FREQUENT_ACCESS = "frequent_access"
    THEFT_ATTEMPT = "theft_attempt"
    POLICY_VIOLATION = "policy_violation"


class GuildVault:
    """
    Represents a guild's secure resource storage facility.
    
    Manages shared resources, access controls, security measures, and transaction
    logging for guild members. Integrates with guild governance and security systems.
    """
    
    def __init__(self,
                 vault_id: str,
                 owner_guild_id: str,
                 vault_location: Union[Tuple[float, float], str] = "guild_hall",
                 security_level: str = SecurityLevel.STANDARD.value):
        """
        Initialize a new guild vault.
        
        Args:
            vault_id: Unique identifier for the vault
            owner_guild_id: ID of the owning guild
            vault_location: Physical location (coordinates or facility_id)
            security_level: Initial security configuration
        """
        self.vault_id = vault_id
        self.owner_guild_id = owner_guild_id
        self.vault_location = vault_location
        self.security_level = security_level
        
        # Resource storage
        self.stored_resources: Dict[str, float] = {
            'gold': 0.0,
            'materials': 0.0,
            'tools': 0.0,
            'reagents': 0.0,
            'artifacts': 0.0,
            'documents': 0.0
        }
        
        # Access control system
        self.access_control: Dict[str, str] = {
            'apprentice': AccessLevel.DEPOSIT.value,
            'journeyman': AccessLevel.WITHDRAW_LIMITED.value,
            'master': AccessLevel.WITHDRAW.value,
            'guildmaster': AccessLevel.FULL_ACCESS.value
        }
        
        # Security and monitoring
        self.transaction_log: List[Dict[str, Any]] = []
        self.security_alerts: List[Dict[str, Any]] = []
        self.access_attempts: List[Dict[str, Any]] = []
        self.last_audit_day: int = 0
        
        # Vault characteristics
        self.capacity_limits: Dict[str, float] = {
            'gold': 100000.0,
            'materials': 50000.0,
            'tools': 10000.0,
            'reagents': 5000.0,
            'artifacts': 1000.0,
            'documents': 2000.0
        }
        
        # Security features
        self.theft_resistance: float = self._calculate_theft_resistance()
        self.detection_chance: float = self._calculate_detection_chance()
        self.emergency_lockdown: bool = False
        self.authorized_personnel: List[str] = []  # Special access list
        
        # Daily limits for withdrawals
        self.daily_withdrawal_limits: Dict[str, Dict[str, float]] = {
            AccessLevel.WITHDRAW_LIMITED.value: {
                'gold': 100.0,
                'materials': 50.0,
                'tools': 10.0,
                'reagents': 5.0
            },
            AccessLevel.WITHDRAW.value: {
                'gold': 1000.0,
                'materials': 500.0,
                'tools': 100.0,
                'reagents': 50.0
            }
        }
        
        # Track daily usage
        self.daily_usage: Dict[str, Dict[str, float]] = {}
        self.current_day: int = 0
    
    def _calculate_theft_resistance(self) -> float:
        """Calculate vault's resistance to theft attempts."""
        security_multipliers = {
            SecurityLevel.MINIMAL.value: 0.2,
            SecurityLevel.BASIC.value: 0.4,
            SecurityLevel.STANDARD.value: 0.6,
            SecurityLevel.HIGH.value: 0.8,
            SecurityLevel.MAXIMUM.value: 0.95
        }
        return security_multipliers.get(self.security_level, 0.6)
    
    def _calculate_detection_chance(self) -> float:
        """Calculate chance of detecting unauthorized access."""
        detection_rates = {
            SecurityLevel.MINIMAL.value: 0.1,
            SecurityLevel.BASIC.value: 0.3,
            SecurityLevel.STANDARD.value: 0.5,
            SecurityLevel.HIGH.value: 0.7,
            SecurityLevel.MAXIMUM.value: 0.9
        }
        return detection_rates.get(self.security_level, 0.5)
    
    def update_daily_limits(self, current_day: int) -> None:
        """Reset daily withdrawal tracking."""
        if current_day != self.current_day:
            self.daily_usage = {}
            self.current_day = current_day
    
    def check_access_permission(self, actor_id: str, actor_rank: str, transaction_type: str) -> bool:
        """
        Check if actor has permission for the requested transaction.
        
        Args:
            actor_id: ID of the actor attempting access
            actor_rank: Guild rank of the actor
            transaction_type: Type of transaction requested
            
        Returns:
            True if access is permitted
        """
        if self.emergency_lockdown and actor_id not in self.authorized_personnel:
            return False
        
        access_level = self.access_control.get(actor_rank, AccessLevel.NONE.value)
        
        if transaction_type == TransactionType.DEPOSIT.value:
            return access_level in [
                AccessLevel.DEPOSIT.value,
                AccessLevel.WITHDRAW_LIMITED.value,
                AccessLevel.WITHDRAW.value,
                AccessLevel.FULL_ACCESS.value
            ]
        
        elif transaction_type == TransactionType.WITHDRAWAL.value:
            return access_level in [
                AccessLevel.WITHDRAW_LIMITED.value,
                AccessLevel.WITHDRAW.value,
                AccessLevel.FULL_ACCESS.value
            ]
        
        elif transaction_type == TransactionType.TRANSFER.value:
            return access_level in [
                AccessLevel.WITHDRAW.value,
                AccessLevel.FULL_ACCESS.value
            ]
        
        elif transaction_type in [TransactionType.CONFISCATION.value, TransactionType.AUDIT_ADJUSTMENT.value]:
            return access_level == AccessLevel.FULL_ACCESS.value
        
        return False
    
    def check_daily_limit(self, actor_id: str, actor_rank: str, resource: str, quantity: float) -> bool:
        """Check if withdrawal is within daily limits."""
        access_level = self.access_control.get(actor_rank, AccessLevel.NONE.value)
        
        if access_level == AccessLevel.FULL_ACCESS.value:
            return True  # No limits for full access
        
        limits = self.daily_withdrawal_limits.get(access_level, {})
        daily_limit = limits.get(resource, 0.0)
        
        if daily_limit == 0.0:
            return False  # No permission for this resource
        
        # Check current daily usage
        if actor_id not in self.daily_usage:
            self.daily_usage[actor_id] = {}
        
        current_usage = self.daily_usage[actor_id].get(resource, 0.0)
        
        return (current_usage + quantity) <= daily_limit
    
    def record_transaction(self,
                         actor_id: str,
                         transaction_type: str,
                         resource: str,
                         quantity: float,
                         reason: str,
                         day: int,
                         success: bool = True) -> None:
        """Record a vault transaction in the log."""
        
        transaction = {
            'transaction_id': str(uuid.uuid4()),
            'actor_id': actor_id,
            'type': transaction_type,
            'resource': resource,
            'quantity': quantity,
            'reason': reason,
            'day': day,
            'timestamp': datetime.now(),
            'success': success,
            'vault_balance_after': self.stored_resources.get(resource, 0.0)
        }
        
        self.transaction_log.append(transaction)
        
        # Update daily usage tracking
        if success and transaction_type == TransactionType.WITHDRAWAL.value:
            if actor_id not in self.daily_usage:
                self.daily_usage[actor_id] = {}
            
            current_usage = self.daily_usage[actor_id].get(resource, 0.0)
            self.daily_usage[actor_id][resource] = current_usage + quantity
    
    def generate_security_alert(self,
                               alert_type: str,
                               actor_id: str,
                               details: Dict[str, Any],
                               day: int) -> None:
        """Generate a security alert for suspicious activity."""
        
        alert = {
            'alert_id': str(uuid.uuid4()),
            'type': alert_type,
            'actor_id': actor_id,
            'details': details,
            'day': day,
            'timestamp': datetime.now(),
            'resolved': False,
            'severity': self._calculate_alert_severity(alert_type, details)
        }
        
        self.security_alerts.append(alert)
    
    def _calculate_alert_severity(self, alert_type: str, details: Dict[str, Any]) -> str:
        """Calculate the severity level of a security alert."""
        
        if alert_type == VaultAlert.THEFT_ATTEMPT.value:
            return "critical"
        elif alert_type == VaultAlert.UNAUTHORIZED_ACCESS.value:
            return "high"
        elif alert_type == VaultAlert.LARGE_TRANSACTION.value:
            amount = details.get('quantity', 0.0)
            if amount > 1000.0:
                return "high"
            elif amount > 500.0:
                return "medium"
            else:
                return "low"
        elif alert_type == VaultAlert.SUSPICIOUS_WITHDRAWAL.value:
            return "medium"
        else:
            return "low"
    
    def get_vault_summary(self) -> Dict[str, Any]:
        """Get comprehensive vault status summary."""
        
        total_value = sum(self.stored_resources.values())
        recent_transactions = [t for t in self.transaction_log if 
                             (datetime.now() - t['timestamp']).days <= 7]
        
        return {
            'vault_id': self.vault_id,
            'owner_guild_id': self.owner_guild_id,
            'security_level': self.security_level,
            'total_value': total_value,
            'resources': self.stored_resources.copy(),
            'capacity_utilization': {
                resource: (amount / self.capacity_limits[resource]) * 100
                for resource, amount in self.stored_resources.items()
            },
            'recent_transaction_count': len(recent_transactions),
            'active_alerts': len([a for a in self.security_alerts if not a['resolved']]),
            'emergency_lockdown': self.emergency_lockdown,
            'last_audit_day': self.last_audit_day
        }


def deposit_to_vault(guild: 'LocalGuild',
                    vault: GuildVault,
                    actor_id: str,
                    actor_rank: str,
                    resource: str,
                    quantity: float,
                    reason: str,
                    day: int) -> Dict[str, Any]:
    """
    Deposit resources to the guild vault.
    
    Args:
        guild: Guild object containing vault
        vault: GuildVault object
        actor_id: ID of the depositing actor
        actor_rank: Guild rank of the actor
        resource: Type of resource being deposited
        quantity: Amount to deposit
        reason: Reason for the deposit
        day: Current simulation day
        
    Returns:
        Dictionary containing transaction result and details
    """
    
    result = {
        'success': False,
        'reason': '',
        'transaction_id': None,
        'alerts_generated': [],
        'vault_balance': vault.stored_resources.get(resource, 0.0)
    }
    
    # Update daily limits
    vault.update_daily_limits(day)
    
    # Check access permissions
    if not vault.check_access_permission(actor_id, actor_rank, TransactionType.DEPOSIT.value):
        result['reason'] = 'insufficient_permissions'
        vault.record_transaction(actor_id, TransactionType.DEPOSIT.value, resource, 
                               quantity, reason, day, False)
        return result
    
    # Check capacity limits
    current_amount = vault.stored_resources.get(resource, 0.0)
    capacity_limit = vault.capacity_limits.get(resource, float('inf'))
    
    if current_amount + quantity > capacity_limit:
        result['reason'] = 'capacity_exceeded'
        vault.record_transaction(actor_id, TransactionType.DEPOSIT.value, resource,
                               quantity, reason, day, False)
        return result
    
    # Validate quantity
    if quantity <= 0:
        result['reason'] = 'invalid_quantity'
        return result
    
    # Process deposit
    vault.stored_resources[resource] = current_amount + quantity
    guild.vault_resources[resource] = vault.stored_resources[resource]
    
    # Record transaction
    transaction_id = str(uuid.uuid4())
    vault.record_transaction(actor_id, TransactionType.DEPOSIT.value, resource,
                           quantity, reason, day, True)
    
    # Update guild vault log
    guild.vault_log.append({
        'transaction_id': transaction_id,
        'actor_id': actor_id,
        'type': TransactionType.DEPOSIT.value,
        'resource': resource,
        'quantity': quantity,
        'reason': reason,
        'day': day,
        'timestamp': datetime.now()
    })
    
    # Check for alerts
    if quantity > 500.0:  # Large deposit
        vault.generate_security_alert(
            VaultAlert.LARGE_TRANSACTION.value,
            actor_id,
            {'resource': resource, 'quantity': quantity, 'type': 'deposit'},
            day
        )
        result['alerts_generated'].append('large_transaction')
    
    result['success'] = True
    result['transaction_id'] = transaction_id
    result['vault_balance'] = vault.stored_resources[resource]
    
    return result


def withdraw_from_vault(guild: 'LocalGuild',
                       vault: GuildVault,
                       actor_id: str,
                       actor_rank: str,
                       resource: str,
                       quantity: float,
                       reason: str,
                       day: int) -> Dict[str, Any]:
    """
    Withdraw resources from the guild vault.
    
    Args:
        guild: Guild object containing vault
        vault: GuildVault object
        actor_id: ID of the withdrawing actor
        actor_rank: Guild rank of the actor
        resource: Type of resource being withdrawn
        quantity: Amount to withdraw
        reason: Reason for the withdrawal
        day: Current simulation day
        
    Returns:
        Dictionary containing transaction result and details
    """
    
    result = {
        'success': False,
        'reason': '',
        'transaction_id': None,
        'alerts_generated': [],
        'vault_balance': vault.stored_resources.get(resource, 0.0)
    }
    
    # Update daily limits
    vault.update_daily_limits(day)
    
    # Check access permissions
    if not vault.check_access_permission(actor_id, actor_rank, TransactionType.WITHDRAWAL.value):
        result['reason'] = 'insufficient_permissions'
        vault.record_transaction(actor_id, TransactionType.WITHDRAWAL.value, resource,
                               quantity, reason, day, False)
        
        # Generate unauthorized access alert
        vault.generate_security_alert(
            VaultAlert.UNAUTHORIZED_ACCESS.value,
            actor_id,
            {'attempted_resource': resource, 'attempted_quantity': quantity},
            day
        )
        result['alerts_generated'].append('unauthorized_access')
        return result
    
    # Check daily limits
    if not vault.check_daily_limit(actor_id, actor_rank, resource, quantity):
        result['reason'] = 'daily_limit_exceeded'
        vault.record_transaction(actor_id, TransactionType.WITHDRAWAL.value, resource,
                               quantity, reason, day, False)
        return result
    
    # Check available resources
    current_amount = vault.stored_resources.get(resource, 0.0)
    if current_amount < quantity:
        result['reason'] = 'insufficient_resources'
        vault.record_transaction(actor_id, TransactionType.WITHDRAWAL.value, resource,
                               quantity, reason, day, False)
        return result
    
    # Validate quantity
    if quantity <= 0:
        result['reason'] = 'invalid_quantity'
        return result
    
    # Process withdrawal
    vault.stored_resources[resource] = current_amount - quantity
    guild.vault_resources[resource] = vault.stored_resources[resource]
    
    # Record transaction
    transaction_id = str(uuid.uuid4())
    vault.record_transaction(actor_id, TransactionType.WITHDRAWAL.value, resource,
                           quantity, reason, day, True)
    
    # Update guild vault log
    guild.vault_log.append({
        'transaction_id': transaction_id,
        'actor_id': actor_id,
        'type': TransactionType.WITHDRAWAL.value,
        'resource': resource,
        'quantity': quantity,
        'reason': reason,
        'day': day,
        'timestamp': datetime.now()
    })
    
    # Check for alerts
    alerts = []
    
    # Large withdrawal alert
    if quantity > 500.0:
        vault.generate_security_alert(
            VaultAlert.LARGE_TRANSACTION.value,
            actor_id,
            {'resource': resource, 'quantity': quantity, 'type': 'withdrawal'},
            day
        )
        alerts.append('large_transaction')
    
    # Frequent access alert
    recent_transactions = [t for t in vault.transaction_log 
                         if t['actor_id'] == actor_id and 
                         t['day'] >= day - 1 and t['success']]
    
    if len(recent_transactions) > 5:
        vault.generate_security_alert(
            VaultAlert.FREQUENT_ACCESS.value,
            actor_id,
            {'transaction_count': len(recent_transactions), 'timeframe': '24_hours'},
            day
        )
        alerts.append('frequent_access')
    
    # Suspicious pattern detection
    if _detect_suspicious_pattern(vault, actor_id, resource, quantity, day):
        vault.generate_security_alert(
            VaultAlert.SUSPICIOUS_WITHDRAWAL.value,
            actor_id,
            {'resource': resource, 'quantity': quantity, 'pattern': 'unusual_behavior'},
            day
        )
        alerts.append('suspicious_withdrawal')
    
    result['success'] = True
    result['transaction_id'] = transaction_id
    result['vault_balance'] = vault.stored_resources[resource]
    result['alerts_generated'] = alerts
    
    return result


def audit_vault_transactions(guild: 'LocalGuild',
                            vault: GuildVault,
                            audit_period_days: int = 30) -> Dict[str, Any]:
    """
    Audit vault transactions for irregularities and suspicious activity.
    
    Args:
        guild: Guild object containing vault
        vault: GuildVault object
        audit_period_days: Number of days to audit
        
    Returns:
        Dictionary containing audit results and recommendations
    """
    
    current_day = vault.current_day
    audit_start_day = current_day - audit_period_days
    
    # Get transactions in audit period
    audit_transactions = [
        t for t in vault.transaction_log 
        if t['day'] >= audit_start_day and t['success']
    ]
    
    audit_result = {
        'audit_period': f"{audit_start_day} to {current_day}",
        'total_transactions': len(audit_transactions),
        'irregularities': [],
        'recommendations': [],
        'actor_analysis': {},
        'resource_analysis': {},
        'security_score': 0.0
    }
    
    # Analyze by actor
    actor_stats = {}
    for transaction in audit_transactions:
        actor_id = transaction['actor_id']
        if actor_id not in actor_stats:
            actor_stats[actor_id] = {
                'deposits': 0,
                'withdrawals': 0,
                'total_deposited': {},
                'total_withdrawn': {},
                'transaction_count': 0
            }
        
        stats = actor_stats[actor_id]
        stats['transaction_count'] += 1
        
        if transaction['type'] == TransactionType.DEPOSIT.value:
            stats['deposits'] += 1
            resource = transaction['resource']
            stats['total_deposited'][resource] = stats['total_deposited'].get(resource, 0.0) + transaction['quantity']
        
        elif transaction['type'] == TransactionType.WITHDRAWAL.value:
            stats['withdrawals'] += 1
            resource = transaction['resource']
            stats['total_withdrawn'][resource] = stats['total_withdrawn'].get(resource, 0.0) + transaction['quantity']
    
    # Identify irregularities
    for actor_id, stats in actor_stats.items():
        # Check for withdrawal-only behavior
        if stats['withdrawals'] > 0 and stats['deposits'] == 0:
            if stats['withdrawals'] > 5:
                audit_result['irregularities'].append({
                    'type': 'withdrawal_only_pattern',
                    'actor_id': actor_id,
                    'withdrawal_count': stats['withdrawals'],
                    'severity': 'medium'
                })
        
        # Check for excessive activity
        if stats['transaction_count'] > 20:
            audit_result['irregularities'].append({
                'type': 'excessive_activity',
                'actor_id': actor_id,
                'transaction_count': stats['transaction_count'],
                'severity': 'low'
            })
        
        # Check for large net withdrawals
        for resource in stats['total_withdrawn']:
            withdrawn = stats['total_withdrawn'][resource]
            deposited = stats['total_deposited'].get(resource, 0.0)
            net_withdrawal = withdrawn - deposited
            
            if net_withdrawal > 1000.0:
                audit_result['irregularities'].append({
                    'type': 'large_net_withdrawal',
                    'actor_id': actor_id,
                    'resource': resource,
                    'net_amount': net_withdrawal,
                    'severity': 'high'
                })
    
    # Resource flow analysis
    resource_flows = {}
    for transaction in audit_transactions:
        resource = transaction['resource']
        if resource not in resource_flows:
            resource_flows[resource] = {'deposited': 0.0, 'withdrawn': 0.0}
        
        if transaction['type'] == TransactionType.DEPOSIT.value:
            resource_flows[resource]['deposited'] += transaction['quantity']
        elif transaction['type'] == TransactionType.WITHDRAWAL.value:
            resource_flows[resource]['withdrawn'] += transaction['quantity']
    
    # Check for resource drain
    for resource, flows in resource_flows.items():
        net_flow = flows['deposited'] - flows['withdrawn']
        if net_flow < -500.0:  # Significant net outflow
            audit_result['irregularities'].append({
                'type': 'resource_drain',
                'resource': resource,
                'net_outflow': abs(net_flow),
                'severity': 'medium'
            })
    
    # Generate recommendations
    if len(audit_result['irregularities']) > 5:
        audit_result['recommendations'].append("Consider increasing vault security level")
    
    if any(i['severity'] == 'high' for i in audit_result['irregularities']):
        audit_result['recommendations'].append("Investigate high-severity irregularities immediately")
    
    # Calculate security score
    base_score = 100.0
    for irregularity in audit_result['irregularities']:
        if irregularity['severity'] == 'high':
            base_score -= 15.0
        elif irregularity['severity'] == 'medium':
            base_score -= 8.0
        elif irregularity['severity'] == 'low':
            base_score -= 3.0
    
    audit_result['security_score'] = max(0.0, base_score)
    audit_result['actor_analysis'] = actor_stats
    audit_result['resource_analysis'] = resource_flows
    
    # Update vault audit tracking
    vault.last_audit_day = current_day
    
    return audit_result


def attempt_vault_theft(guild: 'LocalGuild',
                       vault: GuildVault,
                       thief_id: str,
                       target_resource: str,
                       theft_skill: float,
                       day: int) -> Dict[str, Any]:
    """
    Attempt to steal from the guild vault.
    
    Args:
        guild: Guild object containing vault
        vault: GuildVault object
        thief_id: ID of the thief
        target_resource: Resource being targeted
        theft_skill: Thief's skill level (0.0-1.0)
        day: Current simulation day
        
    Returns:
        Dictionary containing theft attempt results
    """
    
    result = {
        'success': False,
        'detected': False,
        'stolen_amount': 0.0,
        'consequences': [],
        'alerts_generated': []
    }
    
    # Calculate success chance
    base_success_chance = theft_skill * 0.7
    security_penalty = vault.theft_resistance
    final_success_chance = max(0.05, base_success_chance - security_penalty)
    
    # Calculate detection chance
    base_detection_chance = vault.detection_chance
    skill_modifier = (1.0 - theft_skill) * 0.3
    final_detection_chance = min(0.95, base_detection_chance + skill_modifier)
    
    # Attempt theft
    theft_successful = random.random() < final_success_chance
    theft_detected = random.random() < final_detection_chance
    
    result['detected'] = theft_detected
    
    if theft_successful:
        # Determine stolen amount
        available_amount = vault.stored_resources.get(target_resource, 0.0)
        max_theft_amount = min(available_amount * 0.1, 200.0)  # Max 10% or 200 units
        stolen_amount = random.uniform(0.1, 1.0) * max_theft_amount
        
        if stolen_amount > 0:
            vault.stored_resources[target_resource] -= stolen_amount
            guild.vault_resources[target_resource] = vault.stored_resources[target_resource]
            
            result['success'] = True
            result['stolen_amount'] = stolen_amount
    
    # Record attempt
    vault.record_transaction(
        thief_id,
        TransactionType.THEFT.value,
        target_resource,
        result['stolen_amount'],
        "theft_attempt",
        day,
        result['success']
    )
    
    # Generate alerts and consequences
    if theft_detected:
        vault.generate_security_alert(
            VaultAlert.THEFT_ATTEMPT.value,
            thief_id,
            {
                'target_resource': target_resource,
                'success': result['success'],
                'stolen_amount': result['stolen_amount']
            },
            day
        )
        result['alerts_generated'].append('theft_attempt')
        
        # Consequences for detected theft
        if result['success']:
            result['consequences'].append('theft_successful_but_detected')
        else:
            result['consequences'].append('theft_failed_and_detected')
    
    return result


def _detect_suspicious_pattern(vault: GuildVault,
                             actor_id: str,
                             resource: str,
                             quantity: float,
                             day: int) -> bool:
    """Detect suspicious withdrawal patterns."""
    
    # Get recent transactions by this actor
    recent_transactions = [
        t for t in vault.transaction_log
        if t['actor_id'] == actor_id and 
        t['day'] >= day - 7 and 
        t['type'] == TransactionType.WITHDRAWAL.value and
        t['success']
    ]
    
    if len(recent_transactions) < 3:
        return False
    
    # Check for unusual patterns
    # Pattern 1: Gradually increasing withdrawal amounts
    amounts = [t['quantity'] for t in recent_transactions[-3:]]
    if all(amounts[i] < amounts[i+1] for i in range(len(amounts)-1)):
        if amounts[-1] > amounts[0] * 2:  # Final amount is 2x the first
            return True
    
    # Pattern 2: Same resource, same amount, frequent intervals
    same_resource_transactions = [
        t for t in recent_transactions 
        if t['resource'] == resource
    ]
    
    if len(same_resource_transactions) >= 3:
        amounts = [t['quantity'] for t in same_resource_transactions[-3:]]
        if all(abs(amounts[0] - amount) < amounts[0] * 0.1 for amount in amounts):
            return True
    
    return False


def get_vault_quest_opportunities(guild: 'LocalGuild',
                                vault: GuildVault) -> List[Dict[str, Any]]:
    """
    Generate quest opportunities related to guild vaults.
    
    Args:
        guild: Guild object
        vault: GuildVault object
        
    Returns:
        List of quest opportunities
    """
    
    quests = []
    
    # Security-related quests
    if len(vault.security_alerts) > 0:
        unresolved_alerts = [a for a in vault.security_alerts if not a['resolved']]
        if unresolved_alerts:
            quests.append({
                'quest_type': 'vault_security_investigation',
                'title': 'Investigate Vault Security Breach',
                'description': f'Investigate suspicious activity in the {guild.name} vault.',
                'objectives': [
                    'Review security alerts and transaction logs',
                    'Interview suspected individuals',
                    'Implement security improvements'
                ],
                'rewards': ['guild_reputation', 'security_expertise', 'investigation_skills'],
                'difficulty': 'medium'
            })
    
    # Resource management quests
    low_resources = [r for r, amount in vault.stored_resources.items() if amount < 100.0]
    if low_resources:
        quests.append({
            'quest_type': 'vault_resource_gathering',
            'title': 'Replenish Guild Vault',
            'description': f'Gather resources to replenish the {guild.name} vault supplies.',
            'objectives': [
                f'Collect {", ".join(low_resources)}',
                'Organize resource gathering expedition',
                'Secure safe transport to vault'
            ],
            'rewards': ['guild_contribution', 'resource_management', 'logistics_skills'],
            'difficulty': 'easy'
        })
    
    # Audit and governance quests
    if vault.current_day - vault.last_audit_day > 90:
        quests.append({
            'quest_type': 'vault_audit',
            'title': 'Conduct Vault Audit',
            'description': f'Perform comprehensive audit of {guild.name} vault operations.',
            'objectives': [
                'Review all transaction records',
                'Identify irregularities and policy violations',
                'Recommend security improvements'
            ],
            'rewards': ['administrative_skills', 'guild_trust', 'audit_expertise'],
            'difficulty': 'hard'
        })
    
    return quests


def evaluate_vault_security(vault: GuildVault) -> Dict[str, Any]:
    """
    Evaluate overall vault security and provide recommendations.
    
    Args:
        vault: GuildVault object to evaluate
        
    Returns:
        Dictionary containing security assessment
    """
    
    assessment = {
        'overall_score': 0.0,
        'security_level': vault.security_level,
        'strengths': [],
        'weaknesses': [],
        'recommendations': [],
        'risk_factors': []
    }
    
    base_score = 50.0
    
    # Security level assessment
    security_scores = {
        SecurityLevel.MINIMAL.value: 20.0,
        SecurityLevel.BASIC.value: 40.0,
        SecurityLevel.STANDARD.value: 60.0,
        SecurityLevel.HIGH.value: 80.0,
        SecurityLevel.MAXIMUM.value: 95.0
    }
    
    base_score = security_scores.get(vault.security_level, 50.0)
    
    # Recent security incidents
    recent_alerts = [a for a in vault.security_alerts 
                    if (datetime.now() - a['timestamp']).days <= 30]
    
    critical_alerts = [a for a in recent_alerts if a['severity'] == 'critical']
    high_alerts = [a for a in recent_alerts if a['severity'] == 'high']
    
    if critical_alerts:
        base_score -= len(critical_alerts) * 15.0
        assessment['risk_factors'].append(f"{len(critical_alerts)} critical security incidents")
    
    if high_alerts:
        base_score -= len(high_alerts) * 8.0
        assessment['risk_factors'].append(f"{len(high_alerts)} high-severity incidents")
    
    # Access control evaluation
    if len(vault.access_control) > 4:
        assessment['strengths'].append("Comprehensive access control system")
        base_score += 5.0
    else:
        assessment['weaknesses'].append("Limited access control granularity")
        base_score -= 3.0
    
    # Transaction monitoring
    if len(vault.transaction_log) > 100:
        assessment['strengths'].append("Extensive transaction logging")
        base_score += 3.0
    
    # Audit frequency
    days_since_audit = vault.current_day - vault.last_audit_day
    if days_since_audit > 90:
        assessment['weaknesses'].append("Infrequent security audits")
        assessment['recommendations'].append("Conduct regular security audits (monthly)")
        base_score -= 5.0
    
    # Emergency procedures
    if vault.emergency_lockdown:
        assessment['strengths'].append("Emergency lockdown capability")
        base_score += 5.0
    
    # Generate recommendations
    if base_score < 60.0:
        assessment['recommendations'].append("Upgrade vault security level")
    
    if len(recent_alerts) > 5:
        assessment['recommendations'].append("Review and strengthen access policies")
    
    assessment['overall_score'] = max(0.0, min(100.0, base_score))
    
    return assessment 