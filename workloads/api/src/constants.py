from uuid import UUID

# Disabled-auth mode authenticates every request as one shared anonymous user scoped to one shared
# tenant, so a map captured on one device is visible to another and no client needs to send an
# identity header. Both are sentinel UUIDs the personal-tenant trigger's gen_random_uuid() can
# never emit, so neither collides with a real tenant or user.
SHARED_ANONYMOUS_TENANT = UUID("00000000-0000-0000-0000-000000000000")
SHARED_ANONYMOUS_USER = UUID("00000000-0000-0000-0000-000000000001")
