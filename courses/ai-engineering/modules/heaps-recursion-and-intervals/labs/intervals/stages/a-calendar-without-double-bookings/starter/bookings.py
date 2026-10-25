class Calendar:
    """Bookings from a start up to an end, none of them overlapping."""

    def book(self, start, end):
        """Add the booking and return True, or return False if it would overlap one."""
        raise NotImplementedError
