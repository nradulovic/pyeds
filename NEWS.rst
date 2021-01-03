.. This is the project NEWS file which will contain the release notes.

News
====

20.9.0
------

 * Updated contents of README to reflect current state of the library
 * Minor changes around build system
 * Minor library code changes (removed unnecessary name checks)

17.12.0
-------

 * Added Travis build checking support
 * Resource class will check if attribute `name` is valid Python identifier
   and not a reserved word.

0.7.6
-----
 
 * Code cleanups and a lot of code documentation
 * Timers use simpler interface
 * Event class has send() method
 * StateMachine class has additional attributes

0.7.5
-----

 * Removed custom exceptions

0.7.4
-----

 * Minor code documentation
 
0.7.3
-----

 * Minor code documentation

0.7
---
 
 * Added support for event handlers without event argument. These handlers are
   used by state machine events: entry, exit and init.
 * Event object are immutable

0.6
---
 
 *Release date 21-July-2016*
 
 * Hierarchical works as intended

0.5
---

 *Release date: 20-July-2017*

 * Event handlers have 'on_' prefix
 * Added support for Hierarchical FSM
 * All state machines are now executed by Hierarchical FSM dispatcher
 * Removed some error checking, we are using Python's duck taping

0.4
---

 *Release date: 17-July-2017*

 * Fixed StateMachine class appending of new states

0.3
---

*Release date: 11-July-2017*

* Some minor documentation update

0.2
---

*Release date: 11-July-2017*

* Some minor documentation update

0.1
---

*Release date: 11-July-2017*

* First release

