import time

# --- Configuration Constants ---
REPUTATION_THRESHOLD_TO_TRIP = 50  # Reputation score below this trips the circuit
SPAM_COMPLAINT_PENALTY = 20        # Points deducted for a spam complaint
BOUNCE_PENALTY = 5                 # Points deducted for a bounce
OPEN_STATE_COOLDOWN_SECONDS = 10   # Time (seconds) before an OPEN circuit can attempt HALF_OPEN
HALF_OPEN_MAX_TEST_EMAILS = 3      # Max emails to send in HALF_OPEN state for testing

# --- Tenant Data Store (in-memory for this example) ---
tenants = {}

# --- Tenant Class ---
class Tenant:
    def __init__(self, tenant_id):
        self.id = tenant_id
        self.reputation_score = 100  # Start with a perfect reputation
        self.spam_complaints = 0
        self.bounces = 0
        self.circuit_state = "CLOSED" # Possible states: CLOSED, OPEN, HALF_OPEN
        self.last_tripped_time = None
        self.half_open_test_emails_sent = 0

    def __repr__(self):
        return (f"Tenant(ID: {self.id}, Rep: {self.reputation_score}, "
                f"State: {self.circuit_state}, Complaints: {self.spam_complaints}, "
                f"Bounces: {self.bounces})")

# --- Circuit Breaker Logic ---

def _evaluate_reputation_and_trip_if_needed(tenant_id):
    """Checks a tenant's reputation and trips the circuit if it falls below threshold.
    Can trip from CLOSED or HALF_OPEN states."""
    tenant = tenants[tenant_id]
    # If reputation drops below threshold AND circuit is not already OPEN
    if tenant.reputation_score < REPUTATION_THRESHOLD_TO_TRIP and tenant.circuit_state != "OPEN":
        tenant.circuit_state = "OPEN"
        tenant.last_tripped_time = time.time()
        print(f"--- CIRCUIT TRIPPED for Tenant {tenant.id}! Reputation {tenant.reputation_score} is below threshold. ---")

def record_spam_complaint(tenant_id):
    """Simulates a spam complaint for a tenant, reducing their reputation."""
    if tenant_id not in tenants:
        print(f"Error: Tenant {tenant_id} not found.")
        return

    tenant = tenants[tenant_id]
    tenant.spam_complaints += 1
    tenant.reputation_score = max(0, tenant.reputation_score - SPAM_COMPLAINT_PENALTY)
    print(f"[ACTION] Tenant {tenant.id} received a spam complaint. New Rep: {tenant.reputation_score}")
    _evaluate_reputation_and_trip_if_needed(tenant_id) # Check if this action trips the circuit

def record_bounce(tenant_id):
    """Simulates a hard bounce for a tenant, reducing their reputation."""
    if tenant_id not in tenants:
        print(f"Error: Tenant {tenant_id} not found.")
        return

    tenant = tenants[tenant_id]
    tenant.bounces += 1
    tenant.reputation_score = max(0, tenant.reputation_score - BOUNCE_PENALTY)
    print(f"[ACTION] Tenant {tenant.id} received a bounce. New Rep: {tenant.reputation_score}")
    _evaluate_reputation_and_trip_if_needed(tenant_id) # Check if this action trips the circuit

def attempt_send_email(tenant_id):
    """Attempts to send an email for a tenant, respecting the circuit breaker state."""
    if tenant_id not in tenants:
        print(f"Error: Tenant {tenant_id} not found.")
        return False

    tenant = tenants[tenant_id]

    # --- Reputation Circuit Breaker Logic ---
    if tenant.circuit_state == "OPEN":
        # If in OPEN state, check if enough time has passed to attempt a HALF_OPEN state
        if tenant.last_tripped_time and (time.time() - tenant.last_tripped_time > OPEN_STATE_COOLDOWN_SECONDS):
            tenant.circuit_state = "HALF_OPEN"
            tenant.half_open_test_emails_sent = 0
            print(f"--- CIRCUIT for Tenant {tenant.id} is now HALF_OPEN. Attempting limited sends. ---")
        else:
            print(f"[BLOCKED] Tenant {tenant.id}: Circuit is OPEN. Cannot send email. (Rep: {tenant.reputation_score})")
            return False # Blocked

    if tenant.circuit_state == "HALF_OPEN":
        # In HALF_OPEN state, allow a limited number of test emails
        if tenant.half_open_test_emails_sent < HALF_OPEN_MAX_TEST_EMAILS:
            tenant.half_open_test_emails_sent += 1
            print(f"[TEST SEND] Tenant {tenant.id}: Sending test email in HALF_OPEN state ({tenant.half_open_test_emails_sent}/{HALF_OPEN_MAX_TEST_EMAILS}).")
            # If all test emails sent without new issues, assume success and close circuit
            if tenant.half_open_test_emails_sent >= HALF_OPEN_MAX_TEST_EMAILS:
                tenant.circuit_state = "CLOSED"
                # Small reputation recovery for successful half-open phase
                tenant.reputation_score = min(100, tenant.reputation_score + (SPAM_COMPLAINT_PENALTY * 0.5))
                print(f"--- CIRCUIT for Tenant {tenant.id} is now CLOSED. Reputation recovered slightly to {tenant.reputation_score}. ---")
            print(f"[SENT] Email sent successfully for Tenant {tenant.id}. (Rep: {tenant.reputation_score})")
            return True
        else:
            # This path should ideally not be hit if the above logic transitions to CLOSED
            # but as a fallback, if somehow still HALF_OPEN and max tests exceeded, block
            print(f"[BLOCKED] Tenant {tenant.id}: Circuit is HALF_OPEN, but test emails limit reached without full recovery. Blocking.")
            return False

    if tenant.circuit_state == "CLOSED":
        # In CLOSED state, emails can be sent normally
        print(f"[SENT] Email sent successfully for Tenant {tenant.id}. (Rep: {tenant.reputation_score})")
        return True

    return False # Should not be reached

# --- Main Simulation ---
def main():
    # Initialize tenants
    tenants["tenant_A"] = Tenant("tenant_A")
    tenants["tenant_B"] = Tenant("tenant_B")
    tenants["tenant_C"] = Tenant("tenant_C")

    print("--- Initial State ---")
    for tenant_id in tenants:
        print(tenants[tenant_id])
    print("\n" + "="*30 + "\n")

    # Scenario 1: Good tenant sends emails
    print("Scenario 1: Tenant A (good tenant) sends emails.")
    attempt_send_email("tenant_A")
    attempt_send_email("tenant_A")
    print("\n" + "="*30 + "\n")

    # Scenario 2: Bad tenant (Tenant B) starts getting complaints and bounces
    print("Scenario 2: Tenant B (bad tenant) receives multiple spam complaints and bounces.")
    attempt_send_email("tenant_B") # Initial send
    record_spam_complaint("tenant_B") # Rep: 80
    attempt_send_email("tenant_B") # Still CLOSED, but rep is low
    record_bounce("tenant_B")       # Rep: 75
    record_spam_complaint("tenant_B") # Rep: 55
    record_bounce("tenant_B")       # Rep: 50 - CIRCUIT TRIPPED!
    print(tenants["tenant_B"])
    print("\n" + "="*30 + "\n")

    # Scenario 3: Tenant B is now blocked
    print("Scenario 3: Tenant B attempts to send emails while circuit is OPEN.")
    attempt_send_email("tenant_B")
    attempt_send_email("tenant_B")
    print("\n" + "="*30 + "\n")

    # Scenario 4: Other tenants are unaffected
    print("Scenario 4: Tenant C (unaffected) continues to send emails.")
    attempt_send_email("tenant_C")
    attempt_send_email("tenant_C")
    print("\n" + "="*30 + "\n")

    # Scenario 5: Wait for cooldown and attempt HALF_OPEN for Tenant B
    print(f"Scenario 5: Waiting {OPEN_STATE_COOLDOWN_SECONDS} seconds for Tenant B's circuit to attempt HALF_OPEN...")
    time.sleep(OPEN_STATE_COOLDOWN_SECONDS + 1) # Wait a bit more than cooldown
    attempt_send_email("tenant_B") # This should trigger HALF_OPEN and send the first test email
    attempt_send_email("tenant_B") # Second test email
    record_bounce("tenant_B") # Oh no, another issue during HALF_OPEN! This should trip it back to OPEN.
    attempt_send_email("tenant_B") # This will now be blocked as it's back to OPEN
    print(tenants["tenant_B"])
    print("\n" + "="*30 + "\n")

    # Scenario 6: If Tenant B tripped again, wait and try again for full recovery
    if tenants["tenant_B"].circuit_state == "OPEN":
        print(f"Scenario 6: Tenant B tripped again. Waiting {OPEN_STATE_COOLDOWN_SECONDS} seconds to try HALF_OPEN again.")
        time.sleep(OPEN_STATE_COOLDOWN_SECONDS + 1)
        attempt_send_email("tenant_B") # Should go HALF_OPEN (1/3)
        attempt_send_email("tenant_B") # (2/3)
        attempt_send_email("tenant_B") # (3/3) - This should close the circuit if no issues
        attempt_send_email("tenant_B") # Now it should be fully CLOSED and sending normally
        print(tenants["tenant_B"])
        print("\n" + "="*30 + "\n")

    print("--- Final State ---")
    for tenant_id in tenants:
        print(tenants[tenant_id])

if __name__ == "__main__":
    main()
