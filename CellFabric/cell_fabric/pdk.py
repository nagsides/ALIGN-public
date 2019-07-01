import json

class Pdk(object):

    def __init__(self):
        """Initialize empty container dict"""
        self.pdk = {}

    def __str__(self):
        ret = ''
        for key, value in self.pdk.items():
            ret += f"{key}: {value}\n"
        return ret

    def __contains__(self, key):
        return key in self.pdk

    def __getitem__(self, key):
        """Act like a read-only dict"""
        assert key in self.pdk
        return self.pdk[key]

    def items(self):
        """Manage iterators for read-only dict"""
        return self.pdk.items()

    def keys(self):
        """Manage iterators for read-only dict"""
        return self.pdk.keys()

    def values(self):
        """Manage iterators for read-only dict"""
        return self.pdk.values()

    def load(self, filename):
        with open(filename, "rt") as fp:
            j = json.load(fp)
        assert 'Abstraction' in j
        for layer in j['Abstraction']:
            assert layer['Layer'] not in self.pdk, f"Cannot have multiple {layer['Layer']} layers with same name"
            assert layer['Layer'][0].isupper(), f"Layer name {layer['Layer']} must start with capitalized letter"
            if layer['Layer'].startswith('M'):
                self.addMetal(**layer)
            elif layer['Layer'].startswith('V'):
                self.addVia(**layer)
            else:
                self.add(**layer)
        return self

    @staticmethod
    def _check(parameters, **kwargs):
        assert all( x in kwargs for x in parameters), f"Entry {kwargs} missing one or more of {parameters}"
        assert all( x in parameters for x in kwargs.keys()), f"Entry {kwargs} has one or more spurious entries (Needs only {parameters})"

    def _add(self, parameters, **kwargs):
        # Guarantee one is to one mapping between parameters & kwargs
        layername = kwargs.pop('Layer')
        self.pdk[layername] = {key: None if value == 'NA' else value for key, value in kwargs.items()}

    def addMetal(self, **kwargs):
        params = ['Layer',
                  'LayerNo',
                  'Direction',
                  'Color',
                  'Pitch',
                  'Width',
                  'MinL',
                  'MaxL',
                  'EndToEnd',
                  'Offset']
        self._check(params, **kwargs)
        # Attributes that need additional processing
        # 0. Dimensions must be integers or None. Pitch & Width must be even.
        assert all(all(isinstance(y, int) for y in kwargs[x] if y is not None) \
            if isinstance(kwargs[x], list) else isinstance(kwargs[x], int) \
            for x in params[4:] if kwargs[x] is not None), \
            f"One or more of {params[4:]} not an integer in {kwargs}"
        assert all(all(y is not None and y % 2 == 0 for y in kwargs[x]) \
            if isinstance(kwargs[x], list) else kwargs[x] is not None and kwargs[x] % 2 == 0 \
            for x in params[4:6] if kwargs[x] is not None), \
            f"One or more of {params[4:6]} in {kwargs} not a multiple of two"
        # 1. Pitch, Width, MinL, MaxL, EndToEnd of type list
        list_params = params[4:]
        ll = set()
        for param in list_params:
            if isinstance(kwargs[param], list):
                if len(kwargs[param]) == 1:
                    kwargs[param] = kwargs[param][0]
                else:
                    ll.add(len(kwargs[param]))
        assert len(ll) <= 1, f"All lists in {kwargs} must of be same length"
        if len(ll) == 1:
            ll = ll.pop()
            for param in list_params:
                if not isinstance(kwargs[param], list):
                    kwargs[param] = [kwargs[param]] * ll
        # 2. Cast direction must be lowercase & ensure it is either v or h
        kwargs['Direction'] = kwargs['Direction'].lower()
        assert kwargs['Direction'] in ('v', 'h'), f"Invalid Direction {kwargs['Direction']} in {kwargs}"
        self._add(params, **kwargs)

    def addVia(self, **kwargs):
        params = ['Layer',
                  'LayerNo',
                  'Stack',
                  'SpaceX',
                  'SpaceY',
                  'WidthX',
                  'WidthY',
                  'VencA_L',
                  'VencA_H',
                  'VencP_L',
                  'VencP_H',
                  'MinNo',
                  'DesignRules']
        self._check(params, **kwargs)
        # Attributes that need additional processing
        # 0. Dimensions
        assert all(isinstance(kwargs[x], int) for x in params[3:7]), f"One or more of {params[3:7]} not an integer in {kwargs}"
        assert all(kwargs[x] % 2 == 0 for x in params[3:7]), f"One or more of {params[3:7]} in {kwargs} not a multiple of two"
        # 1. Metal Stack
        assert isinstance(kwargs['Stack'], list) and len(kwargs['Stack']) == 2, f"Parameter 'Stack': {kwargs['Stack']} must be a list of size 2"
        assert all(x in self.pdk for x in kwargs['Stack']), f"One or more of metals {kwargs['Stack']} not yet defined."
        # 2. DesignRules
        if isinstance(kwargs['DesignRules'], list):
            for rule in kwargs['DesignRules']:
                self._check(['Name', 'Present', 'Absent'], **rule)
        self._add(params, **kwargs)

    def add(self, **kwargs):
        assert 'Layer' in kwargs, '"Layer" is required parameter for all layers in PDK abstraction'
        self._add(None, **kwargs)

    def get_via_stack(self):
        layer_stack = []
        for l, info in self.pdk.items():
            if l.startswith('V'):
                layer_stack.append( (l, tuple(info['Stack'])) )
        return layer_stack
