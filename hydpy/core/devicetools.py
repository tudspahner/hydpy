# -*- coding: utf-8 -*-
"""This modules implements features related to two types of `devices`,
called `nodes` and `elements` which are the most fundamental means to
structure HydPy projects.
"""
# import...
# ...from standard library
from __future__ import division, print_function
import copy
import struct
import weakref
# ...from site-packages
from matplotlib import pyplot
# ...from HydPy
from hydpy import pub
from hydpy.core import connectiontools
from hydpy.core import objecttools
from hydpy.core import sequencetools
from hydpy.core import autodoctools
from hydpy.cythons import pointerutils


class Keywords(set):
    """Set of keyword arguments used to describe and search for element and
    node objects.

    >>> from hydpy.core.devicetools import Keywords
    >>> from hydpy import dummies
    >>> dummies.keywords = Keywords(['first_keyword', 'second_keyword',
    ...                              'keyword_3', 'keyword_4',
    ...                              'keyboard'])
    >>> dummies.keywords
    Keywords(["first_keyword", "keyboard", "keyword_3", "keyword_4",
              "second_keyword"])
    """

    def __init__(self, names=None):
        if names is None:
            names = []
        self.device = None
        self._check_keywords(names)
        super(Keywords, self).__init__(names)

    def startswith(self, name):
        """Returns a list of all keywords starting with the given string.

        >>> from hydpy import dummies
        >>> dummies.keywords.startswith('keyword')
        ['keyword_3', 'keyword_4']
        """
        return sorted(keyword for keyword in self if keyword.startswith(name))

    def endswith(self, name):
        """Returns a list of all keywords ending with the given string.

        >>> from hydpy import dummies
        >>> dummies.keywords.endswith('keyword')
        ['first_keyword', 'second_keyword']
        """
        return sorted(keyword for keyword in self if keyword.endswith(name))

    def contains(self, name):
        """Returns a list of all keywords containing the given string.

        >>> from hydpy import dummies
        >>> dummies.keywords.contains('keyword')
        ['first_keyword', 'keyword_3', 'keyword_4', 'second_keyword']
        """
        return sorted(keyword for keyword in self if name in keyword)

    def _check_keywords(self, names):
        try:
            for name in names:
                objecttools.valid_variable_identifier(name)
        except ValueError:
            objecttools.augmentexcmessage(
                'While trying to add the keyword `%s` to device `%s`'
                % (name, objecttools.devicename(self)))

    def update(self, names):
        """Before updating, names are checked to be valid variable identifiers.

        >>> from hydpy import dummies
        >>> keywords = dummies.keywords
        >>> keywords.update(['test_1', 'test 2'])
        Traceback (most recent call last):
        ...
        ValueError: While trying to add the keyword `test 2` to device `?`, \
the following error occured: The given name string `test 2` does not define a \
valid variable identifier.  ...

        Note that the first string (`test_1`) is not added, as the second
        one (`test 2`) is invalid:

        >>> keywords
        Keywords(["first_keyword", "keyboard", "keyword_3", "keyword_4",
                  "second_keyword"])

        If the seconds string is corrected, everything works fine:

        >>> keywords.update(['test_1', 'test_2'])
        >>> keywords
        Keywords(["first_keyword", "keyboard", "keyword_3", "keyword_4",
                  "second_keyword", "test_1", "test_2"])
        """
        self._check_keywords(names)
        super(Keywords, self).update(names)

    def add(self, name):
        """Before adding a new name, it is checked to be valid variable identifiers.

        >>> from hydpy import dummies
        >>> keywords = dummies.keywords
        >>> keywords.add('1_test')
        Traceback (most recent call last):
        ...
        ValueError: While trying to add the keyword `1_test` to device `?`, \
the following error occured: The given name string `1_test` does not define a \
valid variable identifier.  ...

        >>> keywords
        Keywords(["first_keyword", "keyboard", "keyword_3", "keyword_4",
                  "second_keyword"])

        If the string is corrected, everything works fine:

        >>> keywords.add('one_test')
        >>> keywords
        Keywords(["first_keyword", "keyboard", "keyword_3", "keyword_4",
                  "one_test", "second_keyword"])
        """
        self._check_keywords([name])
        super(Keywords, self).add(name)

    def __repr__(self):
        with objecttools.repr_.preserve_strings(True):
            return objecttools.assignrepr_list(
                        sorted(self), 'Keywords(', width=70) + ')'

    __dir__ = objecttools.dir_


class Device(object):
    """Base class for class :class:`Element` and class :class:`Node`.

    For framework programmers it is important to know, that all created
    devices are registered.  Besides some other simplifications for
    framework users, this prevents from defining multiple devices with
    the same name (which is not allowed, at the names are supposed to
    be valid object identifiers).

    To show how the registry works, we first start with a clear registry:

    >>> from hydpy import Node
    >>> Node.clear_registry()
    >>> sorted(Node.registered_names())
    []

    Now we initialize two nodes:

    >>> node1 = Node('n1')
    >>> node2 = Node('n2')

    Each time we pass the same names to the constructor of class :class:`Node`,
    the same object is returned:

    >>> node1 is Node('n1')
    True
    >>> node1 is Node('n2')
    False

    You can access all registed nodes via the following class method:

    >>> Node.registered_nodes()
    Nodes("n1", "n2")

    The respective names are directly available via:

    >>> sorted(Node.registered_names())
    ['n1', 'n2']

    It is not recommended under usual circumstances, but you are allowed
    to clear the registry:

    >>> Node.clear_registry()
    >>> Node.registered_nodes()
    Nodes()

    But now there is the danger of creating two differnt nodes with the
    same name, which is very likely to result in strange bugs:

    >>> new_node1 = Node('n1')
    >>> new_node1 is node1
    False
    >>> new_node1 == node1
    True

    The examples above also work for class :class:`Element`, except that
    method `registered_nodes` must be exchanged with method
    `registered_elements`, of course:

    >>> from hydpy import Element
    >>> Element.clear_registry()
    >>> Element('e1').registered_elements()
    Elements("e1")
    """

    _registry = {}
    _selection = {}

    def _get_name(self):
        """Name of the actual device (node or element).

        Names are the identifiers of :class:`Node` and :class:`Element`
        objects.  So define them carefully:

        >>> from hydpy import Node
        >>> node1, node2 = Node('n1'), Node('n2')
        >>> node1 is Node('n1')
        True
        >>> node1 is Node('n2')
        False

        Note that each name name must be a valid variable identifier (see
        function :func:`~hydpy.core.objecttools.valid_variable_identifier`),
        to allow for attribute access:

        >>> from hydpy import Nodes
        >>> nodes = Nodes(node1, 'n2')
        >>> nodes.n1
        Node("n1", variable="Q")

        Invalid variable identifiers result errors like the following:

        >>> node3 = Node('n 3')
        Traceback (most recent call last):
        ...
        ValueError: While trying to initialize a `Node` object with value \
`n 3` of type `str`, the following error occured: The given name string `n 3` \
does not define a valid variable identifier.  ...

        When you change the name of a :class:`Node` and :class:`Element`
        object (only do this for a good reason), the corresponding key of
        all related :class:`Nodes` and :class:`Elements` objects (as well
        as of the internal registry) changes automatically:

        >>> node1.name = 'n1a'
        >>> nodes
        Nodes("n1a", "n2")
        """
        return self._name

    def _set_name(self, name):
        self._check_name(name)
        _handlers = self._handlers.copy()
        for handler in _handlers:
            handler.remove_device(self)
        try:
            del self._registry[self._name]
        except KeyError:
            pass
        else:
            self._registry[name] = self
        self._name = name
        for handler in _handlers:
            handler.add_device(self)

    name = property(_get_name, _set_name)

    def _check_name(self, name):
        try:
            objecttools.valid_variable_identifier(name)
        except ValueError:
            objecttools.augmentexcmessage(
                'While trying to initialize a `%s` object with value `%s` '
                'of type `%s`' % (objecttools.classname(self), name,
                                  objecttools.classname(name)))

    def _get_keywords(self):
        """Keywords describing this device.

        The keywords are contained within a :class:`Keywords` object:

        >>> from hydpy import Node
        >>> node = Node('n')
        >>> node.keywords
        Keywords([])

        You are allowed to add then individually...

        >>> node.keywords = 'word1'

        ... or within iterables:

        >>> node.keywords = ('word2', 'word3')
        >>> node.keywords
        Keywords(["word1", "word2", "word3"])

        You can delete all keywords at once via:

        >>> del node.keywords
        >>> node.keywords
        Keywords([])
        """
        return self._keywords

    def _set_keywords(self, keywords):
        keywords = tuple(objecttools.extract(keywords, (str,), True))
        self._keywords.update(keywords)

    def _del_keywords(self):
        self._keywords.clear()

    keywords = property(_get_keywords, _set_keywords, _del_keywords)

    @classmethod
    def clear_registry(cls):
        """Clear the registry from all initialized devices."""
        cls._selection.clear()
        cls._registry.clear()

    @classmethod
    def registered_names(cls):
        """Get all names of :class:`Device` objects initialized so far."""
        return cls._registry.keys()

    def add_handler(self, handler):
        """Add the given handler (either an :class:`Elements` or
        :class`Nodes` object) to the set of handlers stored internally."""
        self._handlers.add(handler)

    def remove_handler(self, handler):
        """Remove the given handler (either an :class:`Elements` or
        :class`Nodes` object) from the set of handlers stored internally."""
        self._handlers.remove(handler)

    def __iter__(self):
        for (key, value) in vars(self).items():
            if isinstance(value, connectiontools.Connections):
                yield (key, value)

    def __lt__(self, other):
        return self.name < other.name

    def __le__(self, other):
        return self.name <= other.name

    def __eq__(self, other):
        return self.name == other.name

    def __ne__(self, other):
        return self.name != other.name

    def __ge__(self, other):
        return self.name >= other.name

    def __gt__(self, other):
        return self.name > other.name

    def __hash__(self):
        return id(self)

    def __str__(self):
        return self.name

    __dir__ = objecttools.dir_


class Node(Device):
    """Handles the data flow between :class:`Element` objects.

    When initializing :class:`Node` objects, values for the optional `variable`
    and `keywords` can be passed, which default to `Q` and "empty:

    >>> from hydpy import Node
    >>> node = Node('test')
    >>> node.variable
    'Q'
    >>> node.keywords
    Keywords([])

    You are allowed to add further keywords by successive constructor calls:

    >>> node = Node('test', keywords='word1')
    >>> Node('test', keywords=('word2', 'word3'))
    Node("test", variable="Q",
         keywords=["word1", "word2", "word3"])

    But you are not allowed to change the variable a node is supposed to
    handle (would be to error-prone):

    >>> Node('test', variable='W')
    Traceback (most recent call last):
    ...
    ValueError: The variable to be represented by a `Node instance cannot \
be changed.  The variable of node `test` is `Q` instead of `W` or `None`.  \
Keep in mind, that `name` is the unique identifier of node objects.

    If you really want to change a variable without to restart your Python
    process, you have to delete the node from the registry first (again,
    very error-prone unless you are absolutely sure you can delete all
    other relevant references to the node object):

    >>> del node._registry['test']
    >>> Node('test', variable='W')
    Node("test", variable="W")


    To fully understand the last example, read the technical remarks
    regarding the registry of :class:`Device` objects explained above.
    On top of this persistent registry, there is also a temporal one,
    which helps to identify when certain nodes where created
    (e.g. during the execution of a certain network file).

    To show how this works, we again start with a clear registry:

    >>> Node.clear_registry()

    Firstly, create two nodes:

    >>> node1 = Node('n1')
    >>> node2 = Node('n2')

    Now "gather" these two nodes:

    >>> Node.gather_new_nodes()
    Nodes("n1", "n2")

    This automatically removes the gathered nodes from the temporal registry.
    This can be shown by simply calling the method again:

    >>> Node.gather_new_nodes()
    Nodes()

    Now create a new node (n3) and call the constructor of an already existing
    node again:

    >>> node3 = Node('n3')
    >>> node1 = Node('n1')

    Calling method `gather_new_nodes` again shows that an node is regarded
    as "new", if its constructor has been called:

    >>> Node.gather_new_nodes()
    Nodes("n1", "n3")

    This mechanism allows for redefining the same node in different network
    files while keeping track of all files where it has been defined.

    The following example is just supposed to clarify that the permanent
    registry has not been altered by calling `gather_new_nodes`:

    >>> Node.registered_nodes()
    Nodes("n1", "n2", "n3")
    """
    _registry = {}
    _selection = {}
    _predefinedvariable = 'Q'

    def __new__(cls, value, variable=None, keywords=None):
        """Return an already existing :class:`Node` instance or, if such
        an instance does not exist yet, return a newly created one.
        """
        name = str(value)
        if name not in cls._registry:
            self = object.__new__(Node)
            self._check_name(name)
            self._name = name
            if variable is None:
                self._variable = self._predefinedvariable
            else:
                self._variable = variable
            self._keywords = Keywords()
            self._keywords.device = self
            self.entries = connectiontools.Connections(self)
            self.exits = connectiontools.Connections(self)
            self.sequences = sequencetools.NodeSequences(self)
            self.deploy_mode = 'newsim'
            self._blackhole = None
            self._handlers = weakref.WeakSet()
            cls._registry[name] = self
        cls._selection[name] = cls._registry[name]
        return cls._registry[name]

    def __init__(self, name, variable=None, keywords=None):
        if (variable is not None) and (variable != self.variable):
            raise ValueError(
                'The variable to be represented by a `Node instance cannot be '
                'changed.  The variable of node `%s` is `%s` instead of `%s` '
                'or `None`.  Keep in mind, that `name` is the unique '
                'identifier of node objects.'
                % (self.name, self.variable, variable))
        self.keywords = keywords

    @property
    def variable(self):
        """The variable handled by the respective node instance, e.g. `Q`."""
        return self._variable

    @classmethod
    def registered_nodes(cls):
        """Get all :class:`Node` objects initialized so far."""
        return Nodes(cls._registry.values())

    @classmethod
    def gather_new_nodes(cls):
        """Gather all `new` :class:`Node` objects. :class:`Node` objects
        are deemed to be new if they have been created after the last usage
        of this method.
        """
        nodes = Nodes(cls._selection.values())
        cls._selection.clear()
        return nodes

    def _get_deploy_mode(self):
        """Defines the kind of information a node deploys.

        The following modes are supported:

          * newsim: Deploy the simulated values calculated just recently.
            This is the default mode, where a node receives e.g. a discharge
            value from a upstream element and passes it to the downstream
            element directly.
          * obs: Deploy observed values instead of simulated values.  The
            node still receives the simulated values from its upstream
            element(s).  But it deploys values to its downstream nodes which
            are defined externally.  Usually, these values are observations
            made available within an Sequence file. See module
            :mod:`~hydpy.core.sequencetools` for further information on
            file specifications.
          * oldsim: Simular to mode `obs`.  But it is usually applied when
            a node is supposed to deploy simulated values which have been
            calculated in a previous simulation run and stored in a sequence
            file.

        The technical difference between modes `obs` and `oldsim` is, that
        the external values are either handled by the `obs` or the `sim`
        sequence object.  Hence, if you select the `oldsim` mode, the
        values of the upstream elements calculated within the current
        simulation are not available (e.g. for parameter calibration)
        after the simulation is finished.
        """
        return self._deploy_mode

    def _set_deploy_mode(self, value):
        if value == 'newsim':
            self.sequences.sim.use_ext = False
        elif value == 'obs':
            self.sequences.sim.use_ext = False
            self.sequences.obs.use_ext = True
        elif value == 'oldsim':
            self.sequences.sim.use_ext = True
            self._blackhole = pointerutils.Double(0.)
        else:
            raise ValueError(
                'When trying to set the routing mode of node %s, the value '
                '`%s` was given, but only the following values are allowed: '
                '`newsim`, `obs` and `oldsim`.' % (self.name, value))
        self._deploy_mode = value

    deploy_mode = property(_get_deploy_mode, _set_deploy_mode)

    def get_double_via_exits(self):
        """Return the :class:`~hydpy.cythons.pointertools.Double` object that
        is supposed to deploy its value to the downstream elements."""
        if self.deploy_mode != 'obs':
            return self.sequences.fastaccess.sim
        else:
            return self.sequences.fastaccess.obs

    def get_double_via_entries(self):
        """Return the :class:`~hydpy.cythons.pointertools.Double` object that
        is supposed to receive the value(s) of the upstream elements."""
        if self.deploy_mode != 'oldsim':
            return self.sequences.fastaccess.sim
        else:
            return self._blackhole

    def reset(self, idx=None):
        """Reset the actual value of the simulation sequence to zero."""
        self.sequences.fastaccess.sim[0] = 0.

    def _loaddata_sim(self, idx):
        """Load the next sim sequence value (of the given index).

        Used during simulations in Python mode only.
        """
        fastaccess = self.sequences.fastaccess
        if fastaccess._sim_ramflag:
            fastaccess.sim[0] = fastaccess._sim_array[idx]
        elif fastaccess._sim_diskflag:
            raw = fastaccess._sim_file.read(8)
            fastaccess.sim[0] = struct.unpack('d', raw)

    def _savedata_sim(self, idx):
        """Save the last sim sequence value (of the given index).

        Used during simulations in Python mode only.
        """
        fastaccess = self.sequences.fastaccess
        if fastaccess._sim_ramflag:
            fastaccess._sim_array[idx] = fastaccess.sim[0]
        elif fastaccess._sim_diskflag:
            raw = struct.pack('d', fastaccess.sim[0])
            fastaccess._sim_file.write(raw)

    def _loaddata_obs(self, idx):
        """Load the next obs sequence value (of the given index).

        Used during simulations in Python mode only.
        """
        fastaccess = self.sequences.fastaccess
        if fastaccess._obs_ramflag:
            fastaccess.obs[0] = fastaccess._obs_array[idx]
        elif fastaccess._obs_diskflag:
            raw = fastaccess._obs_file.read(8)
            fastaccess.obs[0] = struct.unpack('d', raw)

    def prepare_allseries(self, ramflag=True):
        """Prepare the series objects of both the `sim` and the `obs` sequence.

        Call this method before a simulation run, if you need access to the
        whole time series of the simulated and the observed series after the
        simulation run is finished.

        By default, the series are stored in RAM, which is the faster
        option.  If your RAM is limited, pass the `False` for function
        argument `ramflag` to store the series on disk.
        """
        self.prepare_simseries(ramflag)
        self.prepare_obsseries(ramflag)

    def prepare_simseries(self, ramflag=True):
        """Prepare the series object of the `sim` sequence.

        See method :func:`Node.prepare_allseries` for further information.
        """
        self._prepare_nodeseries('sim', ramflag)

    def prepare_obsseries(self, ramflag=True):
        """Prepare the series object of the `obs` sequence.

        See method :func:`Node.prepare_allseries` for further information.
        """
        self._prepare_nodeseries('obs', ramflag)

    def _prepare_nodeseries(self, seqname, ramflag):
        seq = getattr(self.sequences, seqname)
        if ramflag:
            seq.activate_ram()
        else:
            seq.activate_disk()

    def comparison_plot(self, **kwargs):
        """Plot the series of both the `sim` and (if available) the `obs`
        sequence."""
        for (name, seq) in self.sequences:
            if pyplot.isinteractive():
                name = ' '.join((self.name, name))
            pyplot.plot(seq.series, label=name, **kwargs)
        pyplot.legend()
        variable = self.variable
        if variable == 'Q':
            variable = u'Q [m³/s]'
        pyplot.ylabel(variable)
        if not pyplot.isinteractive():
            pyplot.show()

    def __repr__(self):
        return self.assignrepr()

    def assignrepr(self, prefix=''):
        """Defines the `visual appearence` of :class:`Node` objects.

        You can pass a string which prefixes the string representation.
        """
        lines = ['%sNode("%s", variable="%s",'
                 % (prefix, self.name, self.variable)]
        if self.keywords:
            subprefix = '%skeywords=' % (' '*(len(prefix)+5))
            with objecttools.repr_.preserve_strings(True):
                with objecttools.assignrepr_tuple.always_bracketed(False):
                    line = objecttools.assignrepr_list(
                                sorted(self.keywords), subprefix, width=70)
            lines.append(line + ',')
        lines[-1] = lines[-1][:-1]+')'
        return '\n'.join(lines)


class Element(Device):
    """Handles a :class:`~hydpy.core.modeltools.Model` and connects it to
    other models via :class:`Node` objects.

    You are allowed to pass keywords to the constructor of class
    :class:`Element`, as shown above for class :class:`Node`.

    Additionally, you are allowed to pass different nodes (or names of
    nodes) by successive constructor calls, e.g.:

    >>> from hydpy import Element, Node
    >>> Element('test')
    Element("test")
    >>> Element('test',
    ...         inlets='in1',
    ...         outlets='out1',
    ...         receivers='rec1',
    ...         senders='sen1')
    Element("test",
            inlets="in1",
            outlets="out1",
            receivers="rec1",
            senders="sen1")
    >>> Element('test',
    ...         inlets=('in2', Node('in3')),
    ...         outlets=('out2', Node('out3')),
    ...         receivers=('rec2', Node('rec3')),
    ...         senders=('sen2', Node('sen3')))
    Element("test",
            inlets=["in1", "in2", "in3"],
            outlets=["out1", "out2", "out3"],
            receivers=["rec1", "rec2", "rec3"],
            senders=["sen1", "sen2", "sen3"])

    Reassigning some nodes does no harm:

    >>> Element('test',
    ...         inlets=('in2', Node('in3'), 'in4'),
    ...         outlets=('out2', Node('out3'), 'out4'),
    ...         receivers=('rec2', Node('rec3'), 'rec4'),
    ...         senders=('sen2', Node('sen3'), 'sen4'))
    Element("test",
            inlets=["in1", "in2", "in3", "in4"],
            outlets=["out1", "out2", "out3", "out4"],
            receivers=["rec1", "rec2", "rec3", "rec4"],
            senders=["sen1", "sen2", "sen3", "sen4"])

    But it is verified that an element does not handle the same node as
    an `input` and `output` node or as a `receiver` and a `sender` node:

    >>> Element('test', inlets='out1')
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given inlet node `out1` is already \
defined as an outlet node, which is not allowed.

    >>> Element('test', outlets='in1')
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given outlet node `in1` is already \
defined as an inlet node, which is not allowed.

    >>> Element('test', receivers='sen1')
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given receiver node `sen1` is already \
defined as a sender node, which is not allowed.

    >>> Element('test', senders='rec1')
    Traceback (most recent call last):
    ...
    ValueError: For element `test`, the given sender node `rec1` is already \
defined as a receiver, node which is not allowed.



    Note the technical remarks regarding the permanent registry of
    :class:`Device` objects explained above (which also help to understand
    how the last examples work behind the scenes.)  Additionally, the
    remarks on the temperal registry of :class:`Node` objects also apply
    on :class:`Element` objects.  Without to repeat the whole explanation,
    this can be shown by the following short example:

    >>> from hydpy import Elements
    >>> Element.clear_registry()
    >>> Elements('e1', 'e2').e1.gather_new_elements()
    Elements("e1", "e2")
    >>> Elements('e3', 'e1').e1.gather_new_elements()
    Elements("e1", "e3")
    >>> Element.gather_new_elements()
    Elements()
    >>> Element.registered_elements()
    Elements("e1", "e2", "e3")
    """

    _registry = {}
    _selection = {}

    def __new__(cls, value, inlets=None, outlets=None,
                receivers=None, senders=None, keywords=None):
        """Return an already existing :class:`Element` instance or, if such
        an instance does not exist yet, a new newly created one.
        """
        name = str(value)
        if name not in cls._registry:
            self = object.__new__(Element)
            self._check_name(name)
            self._name = name
            self.inlets = connectiontools.Connections(self)
            self.outlets = connectiontools.Connections(self)
            self.receivers = connectiontools.Connections(self)
            self.senders = connectiontools. Connections(self)
            self._keywords = Keywords()
            self._keywords.device = self
            self.model = None
            self._handlers = weakref.WeakSet()
            cls._registry[name] = self
        cls._selection[name] = cls._registry[name]
        return cls._registry[name]

    def __init__(self, name, inlets=None, outlets=None,
                 receivers=None, senders=None, keywords=None):
        """Add the given :class:`Node` objects via the corresponding
        :class:`~hydpy.core.connectiontools.Connection` objects."""
        if inlets is not None:
            for inlet in Nodes(inlets):
                if inlet in self.outlets:
                    raise ValueError(
                        'For element `%s`, the given inlet node `%s` is '
                        'already defined as an outlet node, which is not '
                        'allowed.' % (self, inlet))
                self.inlets += inlet
                inlet.exits += self
        if outlets is not None:
            for outlet in Nodes(outlets):
                if outlet in self.inlets:
                    raise ValueError(
                        'For element `%s`, the given outlet node `%s` is '
                        'already defined as an inlet node, which is not '
                        'allowed.' % (self, outlet))
                self.outlets += outlet
                outlet.entries += self
        if receivers is not None:
            for receiver in Nodes(receivers):
                if receiver in self.senders:
                    raise ValueError(
                        'For element `%s`, the given receiver node `%s` is '
                        'already defined as a sender node, which is not '
                        'allowed.' % (self, receiver))
                self.receivers += receiver
                receiver.exits += self
        if senders is not None:
            for sender in Nodes(senders):
                if sender in self.receivers:
                    raise ValueError(
                        'For element `%s`, the given sender node `%s` is '
                        'already defined as a receiver, node which is not '
                        'allowed.' % (self, sender))
                self.senders += sender
                sender.entries += self
        self.keywords = keywords

    @classmethod
    def registered_elements(cls):
        """Get all :class:`Element` objects initialized so far."""
        return Elements(cls._registry.values())

    @classmethod
    def gather_new_elements(cls):
        """Gather all `new` :class:`Element` objects. :class:`Element` objects
        are deemed to be new if they have been created after the last usage
        of this method.
        """
        elements = Elements(cls._selection.values())
        cls._selection.clear()
        return elements

    @property
    def variables(self):
        """A set of all different variables of the nodes directly connected
        to this element.

        Suppose there is a element connected to five nodes, which (partly)
        represent different variables:

        >>> from hydpy import Element, Node
        >>> element = Element('Test',
        ...                   inlets=(Node('N1', 'X'), Node('N2', 'Y1')),
        ...                   outlets=(Node('N3', 'X'), Node('N4', 'Y2')),
        ...                   receivers=(Node('N5', 'X'), Node('N6', 'Y3')),
        ...                   senders=(Node('N7', 'X'), Node('N8', 'Y4')))

        `variables` puts all the different variables of these nodes together:

        >>> sorted(element.variables)
        ['X', 'Y1', 'Y2', 'Y3', 'Y4']
        """
        variables = set()
        for (name, connections) in self:
            variables.update(connections.variables)
        return variables

    def init_model(self):
        """Initialize the model to be handled by this element and build
        the required connections."""
        dict_ = pub.controlmanager.loadfile(element=self)
        self.connect(dict_['model'])

    def connect(self, model=None):
        """Connect the handled model with this element.

        The following examples involve an error that is catched cleanly
        only in pure Python mode, hence Cython is disabled:

        >>> from hydpy import pub
        >>> pub.options.usecython = False

        If a model is passed, proper connections with this model are build
        We use the "HBV branch model" :mod:`~hydpy.models.hbranch as an
        example, which branches a single input value (from to node `inp`)
        to multiple outputs (nodes `out1` and `out2`):

        >>> from hydpy import Element, Node
        >>> element = Element('a_branch',
        ...                   inlets='branch_input',
        ...                   outlets=('branch_output_1', 'branch_output_2'))
        >>> inp = element.inlets.branch_input
        >>> out1, out2 = element.outlets
        >>> from hydpy.models.hbranch import *
        >>> parameterstep()
        >>> element.connect(model)

        To show that the inlet connection is built properly, assign a new
        value to the inlet node and verify that his value can actually be
        picked by the model:

        >>> inp.sequences.sim = 999.0
        >>> model.pick_input()
        >>> fluxes.input
        input(999.0)

        If no model is passed to method `connect`, the connections with
        the model already handled by this element are refreshed.  In the
        given example, the `hbranch` model could already le to connected
        to its inlet node, but not to its outlet nodes, which requires
        some parameter information on how to allocate the inflow to the
        different outlet nodes:

        >>> xpoints(0.0, 3.0)
        >>> ypoints(branch_output_1=[0.0, 1.0], branch_output_2=[0.0, 2.0])
        >>> parameters.update()
        >>> model.doit(0)
        Traceback (most recent call last):
        ...
        RuntimeError: The pointer of the acutal `PPDouble` instance at \
index 0 requested, but not prepared yet via `setpointer`.

        The last command resulted in a somewhat strange error message.  The
        reason for the explained error is that the `hbranch` model does now
        know how to connect to the outlet nodes `out1` and `out2`, but has
        not been requested to do so.  When we do so, no error is raised:

        >>> element.connect()
        >>> parameters.update()
        >>> model.doit(0)

        Now we can prove that both the inlet and the outlet connections are
        build properly by verifying that the expected output values are
        actually passed to the outlet nodes while performing an simulation
        step with method `doit` above:

        >>> out1.sequences.sim
        sim(333.0)
        >>> out2.sequences.sim
        sim(666.0)


        If neither a model is passed nor an model is already handled, an
        erro is raised:

        >>> Element('empty').connect()
        Traceback (most recent call last):
        ...
        AttributeError: While trying to build the connections of the model \
handled by element `empty`, the following error occured: No model has been \
assigned to the element so far.
        """
        if model is not None:
            self.model = model
            model.element = self
        try:
            model = getattr(self, 'model', None)
            if model is None:
                raise AttributeError(
                    'No model has been assigned to the element so far.')
            else:
                self.model.connect()
        except BaseException:
            objecttools.augmentexcmessage(
                'While trying to build the connections of the model handled '
                'by element `%s`' % self.name)

    def prepare_allseries(self, ramflag=True):
        """Prepare the series objects of all `input`, `flux` and `state`
        sequences of the model handled by this element.

        Call this method before a simulation run, if you need access to
        (nearly) all simulated series of the handled model after the
        simulation run is finished.

        By default, the series are stored in RAM, which is the faster
        option.  If your RAM is limited, pass the `False` for function
        argument `ramflag` to store the series on disk.
        """
        self.prepare_inputseries(ramflag)
        self.prepare_fluxseries(ramflag)
        self.prepare_stateseries(ramflag)

    def prepare_inputseries(self, ramflag=True):
        """Prepare the series objects of the `input` sequences of the model
        handled by this element.

        See method :func:`Element.prepare_allseries` for further information.
        """
        self._prepare_series('inputs', ramflag)

    def prepare_fluxseries(self, ramflag=True):
        """Prepare the series objects of the `flux` sequences of the model
        handled by this element.

        See method :func:`Element.prepare_allseries` for further information.
        """
        self._prepare_series('fluxes', ramflag)

    def prepare_stateseries(self, ramflag=True):
        """Prepare the series objects of the `state` sequences of the model
        handled by this element.

        See method :func:`Element.prepare_allseries` for further information.
        """
        self._prepare_series('states', ramflag)

    def _prepare_series(self, name_subseqs, ramflag):
        sequences = self.model.sequences
        subseqs = getattr(sequences, name_subseqs, None)
        if subseqs:
            if ramflag:
                subseqs.activate_ram()
            else:
                subseqs.activate_disk()

    def _plot(self, subseqs, names, kwargs):
        if names is not None:
            subseqs = ((name, getattr(name)) for name in names)
        for seq in subseqs:
            if seq.NDIM == 0:
                label = kwargs.pop('label', ' '.join((self.name, seq.name)))
                pyplot.plot(seq.series, label=label, **kwargs)
                pyplot.legend()
            else:
                color = kwargs.pop('color', kwargs.pop('c', 'red'))
                pyplot.plot(seq.series, color=color, **kwargs)
        if not pyplot.isinteractive():
            pyplot.show()

    def input_plot(self, names=None, **kwargs):
        """Plot the `input` series of the handled model.

        To plot the series of a subset of all sequences, pass the respective
        names.
        """
        self._plot(self.model.sequences.inputs, names, kwargs)

    def flux_plot(self, names=None, **kwargs):
        """Plot the `flux` series of the handled model.

        To plot the series of a subset of all sequences, pass the respective
        names.
        """
        self._plot(self.model.sequences.fluxes, names, kwargs)

    def state_plot(self, names=None, **kwargs):
        """Plot the `state` series of the handled model.

        To plot the series of a subset of all sequences, pass the respective
        names.
        """
        self._plot(self.model.sequences.states, names, kwargs)

    def assignrepr(self, prefix):
        """Defines the `visual appearence` of :class:`Element` objects.

        You can pass a string which prefixes the string representation.
        """
        with objecttools.repr_.preserve_strings(True):
            with objecttools.assignrepr_tuple.always_bracketed(False):
                blanks = ' ' * (len(prefix) + 8)
                lines = ['%sElement("%s",' % (prefix, self.name)]
                for conname in ('inlets', 'outlets', 'receivers', 'senders'):
                    connections = getattr(self, conname, None)
                    if connections:
                        subprefix = '%s%s=' % (blanks, conname)
                        nodes = [str(node) for node in connections.slaves]
                        line = objecttools.assignrepr_list(
                                                nodes, subprefix, width=70)
                        lines.append(line + ',')
                if self.keywords:
                    subprefix = '%skeywords=' % blanks
                    line = objecttools.assignrepr_list(
                                sorted(self.keywords), subprefix, width=70)
                    lines.append(line + ',')
                lines[-1] = lines[-1][:-1]+')'
                return '\n'.join(lines)

    def __repr__(self):
        return self.assignrepr('')


class Devices(object):
    """Base class for class :class:`Elements` and class :class:`Nodes`.

    There are only small differences between class :class:`Elements`
    and class :class:`Nodes`.  We focus our explanations on class
    :class:`Nodes` arbitrarily.

    The following test objects are used to explain the methods
    and properties of class :class:`Device` (note the different types of
    the initialization arguments):

    >>> from hydpy import dummies
    >>> from hydpy import Node, Nodes, Element, Elements
    >>> dummies.nodes = Nodes('na',
    ...                       Node('nb', variable='W'),
    ...                       Node('nc', keywords=('group_a', 'group_1')),
    ...                       Node('nd', keywords=('group_a', 'group_2')),
    ...                       Node('ne', keywords=('group_b', 'group_1')))
    >>> dummies.elements = Elements('ea', Element('eb'))

    In a nutshell, :class:`Devices` instances are containers supporting
    attribute access.  You can access each device directly by its name:

    >>> nodes = dummies.nodes
    >>> nodes.na
    Node("na", variable="Q")

    Wrong device names result in the following error message:

    >>> nodes.na_
    Traceback (most recent call last):
    ...
    AttributeError: The selected Nodes object has neither a `na_` \
attribute nor does it handle a Node object with name or keyword `na_`, \
which could be returned.

    Attribute deleting is supported:

    >>> 'na' in nodes
    True
    >>> del nodes.na
    >>> 'na' in nodes
    False
    >>> del nodes.na
    Traceback (most recent call last):
    ...
    AttributeError: The selected Nodes object has neither a `na` attribute \
nor does it handle a Node object named `na`, which could be deleted.

    However, exemplified by the next example, setting devices as attributes
    "pythonically" could result in inconsistencies and is not allowed
    (see method :func:`~Devices.add_device` instead):

    >>> nodes.NF = Node('nf')
    Traceback (most recent call last):
    ...
    NotImplementedError: Setting attributes of Nodes objects could result \
in confusion whether a new attribute should be handled as a Node object or \
as a "normal" attribute and is thus not support.

    The operators `+`, `+=`, `-` and `-=` support adding and removing
    groups of devices:

    >>> subgroup = Nodes("nc", "ne")

    >>> nodes
    Nodes("nb", "nc", "nd", "ne")
    >>> subgroup
    Nodes("nc", "ne")
    >>> nodes - subgroup
    Nodes("nb", "nd")

    >>> nodes
    Nodes("nb", "nc", "nd", "ne")
    >>> nodes -= subgroup
    >>> nodes
    Nodes("nb", "nd")

    >>> nodes + subgroup
    Nodes("nb", "nc", "nd", "ne")
    >>> nodes
    Nodes("nb", "nd")
    >>> nodes += subgroup
    >>> nodes
    Nodes("nb", "nc", "nd", "ne")

    Trying to add already existing are to remove non existing devices
    does no harm:

    >>> nodes
    Nodes("nb", "nc", "nd", "ne")
    >>> nodes + subgroup
    Nodes("nb", "nc", "nd", "ne")
    >>> nodes - Node('na')
    Nodes("nb", "nc", "nd", "ne")

    Finally, the following "set operators" are supported:

    >>> subgroup < nodes, nodes < subgroup, nodes < nodes
    (True, False, False)
    >>> subgroup <= nodes, nodes <= subgroup, nodes <= nodes
    (True, False, True)
    >>> subgroup == nodes, nodes == subgroup, nodes == nodes
    (False, False, True)
    >>> subgroup != nodes, nodes != subgroup, nodes != nodes
    (True, True, False)
    >>> subgroup >= nodes, nodes >= subgroup, nodes >= nodes
    (False, True, True)
    >>> subgroup > nodes, nodes > subgroup, nodes > nodes
    (False, True, False)
    """

    _contentclass = None

    def __init__(self, *values):
        self.__dict__['_devices'] = {}
        self.__dict__['_shadowed_keywords'] = set()
        try:
            self._extract_values(values)
        except BaseException:
            objecttools.augmentexcmessage(
                'While trying to initialize a `%s` object'
                % objecttools.classname(self))

    def _extract_values(self, values):
        for value in objecttools.extract(
                        values, types=(self._contentclass, str), skip=True):
            self.add_device(value)

    def add_device(self, device):
        """Add the given :class:`Node` or :class:`Element` object.

        >>> from hydpy import Nodes
        >>> nodes = Nodes('old_node')
        >>> nodes.add_device('new_node')
        >>> nodes
        Nodes("new_node", "old_node")

        Note the implementation detail, that each new node knows the
        object it was added to:

        >>> nodes in nodes.new_node._handlers
        True
        """
        device = self._contentclass(device)
        self._devices[device.name] = device
        device.add_handler(self)

    def remove_device(self, device):
        """Remove the given :class:`Node` or :class:`Element` object.

        >>> from hydpy import Node, Nodes
        >>> nodes = Nodes('node_x', 'node_y')
        >>> node_x, node_y = nodes
        >>> nodes.remove_device('node_y')
        >>> nodes
        Nodes("node_x")

        Note the implementation detail, that a new node forgots its
        container object, after it has been removed:

        >>> nodes in node_x._handlers
        True
        >>> nodes in node_y._handlers
        False
        """
        device = self._contentclass(device)
        try:
            del self._devices[device.name]
        except KeyError:
            raise KeyError(
                'The selected %s object does not handle a %s object named '
                '`%s`, which could be removed.'
                % (objecttools.classname(self),
                   objecttools.classname(self._contentclass), device))
        device.remove_handler(self)

    @property
    def names(self):
        """A sorted tuple of the names of the handled devices.

        >>> from hydpy import dummies
        >>> dummies.nodes.names
        ('na', 'nb', 'nc', 'nd', 'ne')
        """
        return tuple(device.name for device in self)

    @property
    def devices(self):
        """A tuple of the handled devices sorted by the device names.

        >>> from hydpy import dummies
        >>> tuple(device.name for device in dummies.nodes.devices)
        ('na', 'nb', 'nc', 'nd', 'ne')
        """
        return tuple(device for device in self)

    @property
    def keywords(self):
        """A set of all keywords of all handled devices.

        In addition to attribute access via device names described above,
        :class:`Device` objects allow for attribute access via keywords.
        This allows for an efficient search of certain groups of devices.
        Lets use the example from above, where the nodes `na` and `nb`
        have no keywords but each of the other three nodes both belongs
        to either `group_a` or `group_b` and `group_1` or `group_2`:

        >>> from hydpy import dummies
        >>> nodes = dummies.nodes
        >>> nodes
        Nodes("na", "nb", "nc", "nd", "ne")
        >>> sorted(nodes.keywords)
        ['group_1', 'group_2', 'group_a', 'group_b']

        If you are interesting in inspecting all nodes belonging to `group_a`,
        build a selection:

        >>> subgroup = nodes.group_1
        >>> subgroup
        Nodes("nc", "ne")

        You can further restrict the search by also selecting the nodes also
        belonging to `group_b`, which holds true for node `ne` only:

        >>> subsubgroup = subgroup.group_b
        >>> subsubgroup
        Nodes("ne")

        Node that the keywords already used for building a subgroup of nodes
        are no informative anymore (as they hold true for each node) and are
        thus not shown anymore:

        >>> sorted(subgroup.keywords)
        ['group_a', 'group_b']
        >>> sorted(subsubgroup.keywords)
        []

        The latter might be confusing, if you intend to work with a subgroup
        of nodes for a longer time.  After copying the subgroup, all keywords
        of the contained devices are available again:

        >>> newgroup = subsubgroup.copy()
        >>> sorted(newgroup.keywords)
        ['group_1', 'group_b']
        """
        return set(keyword for device in self
                   for keyword in device.keywords if
                   keyword not in self._shadowed_keywords)

    def copy(self):
        """Return a shallow copy of the actual :class:`Devices` instance.

        Make a flat copy of the :class:`Nodes` object defined above:

        >>> from hydpy import dummies
        >>> old = dummies.nodes
        >>> import copy
        >>> new = copy.copy(old)

        Show that the copy is not completely flat:

        >>> new == old
        True
        >>> new is old
        False
        >>> new._devices is old._devices
        False
        >>> new.na is new.na
        True

        The private variable `_devices` obviously has also been copied,
        but not the device `na`.  Allowing also to copy devices like `na`
        would be in conflict with using their names as identifiers.
        For this reason deep copying :class:`Devices` objects is disabled:

        >>> copy.deepcopy(dummies.nodes)
        Traceback (most recent call last):
        ...
        NotImplementedError: Deep copying of Nodes objects is not supported, \
as it would require to make deep copies of the Node objects themselves, \
which is in conflict with using their names as identifiers.

        """
        new = type(self)()
        new.__dict__.update(self.__dict__)
        new.__dict__['_devices'] = copy.copy(self._devices)
        new.__dict__['_shadowed_keywords'].clear()
        for device in self:
            device.add_handler(new)
        return new

    __copy__ = copy

    def __deepcopy__(self, dict_):
        classname = objecttools.classname(self)
        raise NotImplementedError(
            'Deep copying of %s objects is not supported, as it would '
            'require to make deep copies of the %s objects themselves, '
            'which is in conflict with using their names as identifiers.'
            % (classname, classname[:-1]))

    def __iter__(self):
        for (name, device) in sorted(self._devices.items()):
            yield device

    def _select_devices_by_keyword(self, name):
        devices = self.__class__(device for device in self if
                                 name in device.keywords)
        devices.__dict__['_shadowed_keywords'] = self._shadowed_keywords.copy()
        devices._shadowed_keywords.add(name)
        return devices

    def __getattr__(self, name):
        try:
            _devices = super(Devices, self).__getattribute__('_devices')
            return _devices[name]
        except KeyError:
            pass
        _devices = self._select_devices_by_keyword(name)
        if len(_devices) > 0:
            return _devices
        else:
            raise AttributeError(
                'The selected %s object has neither a `%s` attribute '
                'nor does it handle a %s object with name or keyword `%s`, '
                'which could be returned.'
                % (objecttools.classname(self), name,
                   objecttools.classname(self._contentclass), name))

    def __setattr__(self, name, value):
        classname = objecttools.classname(self)
        raise NotImplementedError(
            'Setting attributes of %s objects could result in confusion '
            'whether a new attribute should be handled as a %s object or '
            'as a "normal" attribute and is thus not support.'
            % (classname, classname[:-1]))

    def __delattr__(self, name):
        deleted_something = False
        if name in vars(self):
            super(Devices, self).__delattr__(name)
            deleted_something = True
        if name in self._devices:
            self.remove_device(name)
            deleted_something = True
        if not deleted_something:
            raise AttributeError(
                'The selected %s object has neither a `%s` attribute nor does '
                'it handle a %s object named `%s`, which could be deleted.'
                % (objecttools.classname(self), name,
                   objecttools.classname(self._contentclass), name))

    def __contains__(self, device):
        device = self._contentclass(device)
        return device.name in self._devices

    def __len__(self):
        return len(self._devices)

    def __add__(self, values):
        new = self.copy()
        for device in self.__class__(values):
            new.add_device(device)
        return new

    def __iadd__(self, values):
        for device in self.__class__(values):
            self.add_device(device)
        return self

    def __sub__(self, values):
        new = self.copy()
        for device in self.__class__(values):
            try:
                new.remove_device(device)
            except KeyError:
                pass
        return new

    def __isub__(self, values):
        for device in self.__class__(values):
            try:
                self.remove_device(device)
            except KeyError:
                pass
        return self

    def __lt__(self, other):
        return set(self._devices.keys()) < set(other._devices.keys())

    def __le__(self, other):
        return set(self._devices.keys()) <= set(other._devices.keys())

    def __eq__(self, other):
        return set(self._devices.keys()) == set(other._devices.keys())

    def __ne__(self, other):
        return set(self._devices.keys()) != set(other._devices.keys())

    def __ge__(self, other):
        return set(self._devices.keys()) >= set(other._devices.keys())

    def __gt__(self, other):
        return set(self._devices.keys()) > set(other._devices.keys())

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return self.assignrepr('')

    def assignrepr(self, prefix):
        with objecttools.repr_.preserve_strings(True):
            with pub.options.ellipsis(2, optional=True):
                prefix += '%s(' % objecttools.classname(self)
                repr_ = objecttools.assignrepr_values(
                                        self.names, prefix, width=70)
                return repr_ + ')'

    def __dir__(self):
        """Just a regression test:

        >>> from hydpy import dummies
        >>> from hydpy.core.objecttools import assignrepr_values
        >>> print(assignrepr_values(dir(dummies.nodes), '', 70))
        add_device, assignrepr, copy, devices, group_1, group_2, group_a,
        group_b, keywords, na, names, nb, nc, nd, ne, prepare_allseries,
        prepare_obsseries, prepare_simseries, remove_device
        """
        return objecttools.dir_(self) + list(self.names) + list(self.keywords)


class Nodes(Devices):
    """A container for handling :class:`Node` objects."""

    _contentclass = Node

    def prepare_allseries(self, ramflag=True):
        """Call method :func:`~Node.prepare_allseries` of all handled
        elements."""
        self.prepare_simseries(ramflag)
        self.prepare_obsseries(ramflag)

    def prepare_simseries(self, ramflag=True):
        """Call method :func:`~Node.prepare_simseries` of all handled
        elements."""
        for node in self:
            node.prepare_simseries(ramflag)

    def prepare_obsseries(self, ramflag=True):
        """Call method :func:`~Node.prepare_obsseries` of all handled
        elements."""
        for node in self:
            node.prepare_obsseries(ramflag)


class Elements(Devices):
    """A container for handling :class:`Element` objects."""

    _contentclass = Element

    def prepare_allseries(self, ramflag=True):
        """Call method :func:`~Element.prepare_allseries` of all handled
        elements."""
        for element in self:
            element.prepare_allseries(ramflag)

    def prepare_inputseries(self, ramflag=True):
        """Call method :func:`~Element.prepare_inputseries` of all handled
        elements."""
        for element in self:
            element.prepare_inputseries(ramflag)

    def prepare_fluxseries(self, ramflag=True):
        """Call method :func:`~Element.prepare_fluxseries` of all handled
        elements."""
        for element in self:
            element.prepare_fluxseries(ramflag)

    def prepare_stateseries(self, ramflag=True):
        """Call method :func:`~Element.prepare_stateseries` of all handled
        elements."""
        for element in self:
            element.prepare_stateseries(ramflag)


autodoctools.autodoc_module()
