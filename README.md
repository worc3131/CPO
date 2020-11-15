# C(3)PO Communicating Python Objects  

A work in progress...

An attempt the reacreate the occam like CSO library built by my comrade and
 teacher, Bernard Sufrin.
 
https://www.cs.ox.ac.uk/people/bernard.sufrin/personal/CSO/cpa2008-cso-2016revision.pdf
https://www.cs.ox.ac.uk/people/bernard.sufrin/personal/CSO/

As python has fewer available operators than scala, we will map the CSO operators
as follows:

| CSO              | C(3)PO         | Description             |            
|------------------|----------------|-------------------------|
| `c ! x`          | `c << x`       | Write x to channel c | 
| `c ?`            | `~c`           | Read from channel c |  
| `c ? f`          | nyi            | Not implemented. Use f(c?) instead |
| `c ?? f`         | `~c(f)`        | Execute f on the data from channel c in the reader process |
| `proc {expr}`    |<code>@proc<br/>def p():<br/>&nbsp;&nbsp;&nbsp;&nbsp;{expr}</code> | create a process p for which p() is run in the current thread |
| p1 &#124;&#124; p2 &#124;&#124; .. | p1 &#124; p2 &#124; .. | Run each of these processes concurrently only terminating when all of them have terminated |
| p1 &#124;&#124; [p2,p3,..] | p1 &#124; [p2,p3,...] | |
| `run(p)`         | `run(p)`  or `run` | Run p in the current thread |
| `fork(p)`        | `fork(p)` or `@fork` | Run p in a new thread, returning a handle |
| ATTEMPT          | `attempt(f)` or `@attempt` | Attempt to run the function |
| REPEAT           | `repeat(f)` or `@repeat` | Repeatedly run the function |
