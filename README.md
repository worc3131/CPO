# C(3)PO Communicating Python Objects  

A work in progress...

An attempt the reacreate the occam like CSO library built in scala by my comrade
 and teacher, Bernard Sufrin.
 
https://www.cs.ox.ac.uk/people/bernard.sufrin/personal/CSO/cpa2008-cso-2016revision.pdf
https://www.cs.ox.ac.uk/people/bernard.sufrin/personal/CSO/

Pythons concurrency primitives are not as powerful as Scala's, so this library
has less functionality than CSO, whilst some of the other functionality is
essentially simulated rather than being implemented efficiently. Locks 
wihin the python interpreter (the GIL) mean that Python has limited multithreading 
functionality anyway. On the other hand, the fact that python has a loose structure
and is interpreted should make CPO useful for teaching, as the state of the heap
can be inspected as long as the main thread is left free. Finally, the occam syntax 
gives a clean way for python programmers to implement concurrent objects.

As python has fewer available operators than scala, we will map the CSO operators
as follows:

| CSO              | C(3)PO         | Description             |            
|------------------|----------------|-------------------------|
| `c ! x`          | `c << x`       | Write x to channel c | 
| `c ?`            | `~c`           | Read from channel c |  
| `c ? f`          | nyi            | Not implemented. Use f(c?) instead |
| `c ?? f`         | `~c(f)`        | Execute f on the data from channel c in the reader process |
| `proc {expr}`    |<code>@proc<br/>def p(): {expr}</code> | create a process p for which p() is run in the current thread |
| p1 &#124;&#124; p2 &#124;&#124; .. | p1 &#124; p2 &#124; .. | Run each of these processes concurrently only terminating when all of them have terminated |
| p1 &#124;&#124; [p2,p3,..] | p1 &#124; [p2,p3,...] | |
| nyi              | p1 >> p2 >> ... | Run proc p1 then once finished run p2 etc. | 
| `run(p)`         | `run(p)`  or `run` | Run p in the current thread |
| `fork(p)`        | `fork(p)` or `@fork` | Run p in a new thread, returning a handle |
| ATTEMPT          | `attempt(f)` or `@attempt` | Attempt to run the function |
| REPEAT           | `repeat(f)` or `@repeat` | Repeatedly run the function |

