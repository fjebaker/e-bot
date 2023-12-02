`EGameFactory`
==============

This class defines the `EGameFactory` super-class, used to define new interactive 
game components. :py:class:`abstracts.EGameFactory` defines a number of attributes, 
which should be defined by the subclasses. 

.. autoclass:: abstracts.EGameFactory
    :members:
    :undoc-members:
    :exclude-members: execute_rounds

    .. attribute:: game_name
        :type: str
        
        The game name (set by subclass).

    .. attribute:: game_description
        :type: str
        
        A short description of the game (set by subclass).

    .. attribute:: wait_duration
        :type: int
        
        Duration called by :py:func:`asyncio.sleep()` to pace the game (set by subclass).

    .. attribute:: min_players
        :type: int
        
        Minimum number of players required to play the game (set by subclass).

    .. attribute:: cog_help
        :type: str
        
        A help string present to document the available cog commands.
    
    .. attribute:: has_scrape
        :type: str, Optional
        :value: False
        
        A short description of the game (set by subclass).

    ..
        Temporary fix for documenting decorator functions properly
    
    .. autodecorator:: abstracts.EGameFactory.execute_rounds