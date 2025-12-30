class MapObject:
    def __init__(self, obj_type, q, r, **props):
        self.type = obj_type  # e.g., 'star', 'planet', 'enemy', etc.
        self.q = q  # Axial coordinate q
        self.r = r  # Axial coordinate r
        self.props = props  # Additional properties (dict)

    @property
    def faction(self):
        """Get the faction for enemy objects (klingon/romulan). Returns None for non-enemies."""
        return self.props.get('faction', None)

    def __repr__(self):
        return (
            f"<MapObject type={self.type} q={self.q} r={self.r} "
            f"props={self.props}>"
        ) 