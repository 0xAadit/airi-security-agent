Universal Information Security Agents
You should build a team of 2 to 4 people to choose a domain
Task description
Rating
Round results

The AIRI Artificial Intelligence Research Institute is an autonomous, non-profit organization dedicated to fundamental and applied research in artificial intelligence. Currently, over 250 AIRI researchers are involved in the Institute's research projects, working collaboratively with the global developer community, academic, and industrial partners. In 2026, the Institute celebrated its fifth anniversary.

Description of the main stage task
Cybersecurity professionals often work with sensitive data, internal source code and infrastructure in isolated environments where public LLMs and internet access are prohibited. In such environments, local models become the only practical tool, but their effective application for complex information security scenarios remains an unsolved challenge for most teams.

The competition aims to create universal autonomous information security agents capable of reliably solving practical tasks (vulnerability detection, forensics, security flaw remediation, CTF scenarios) under strict resource constraints related to time and tokens. The business value lies in the emergence of reproducible approaches that improve the speed and quality of information security teams' work without the risk of data leakage and using small local LLMs.

 

Participants must develop a universal autonomous cybersecurity agent that runs in an isolated environment and solves a set of practical information security tasks without internet access. The agent is delivered as a .zip archive (at least run.sh and the necessary source files), deployed in the provided runtime image and receives the task instruction text as input. During execution, only local environment resources and the local LLM endpoint are accessible via the LOCAL_AGENT_MODEL, OPENAI_BASE_URL, and OPENAI_API_KEY environment variables; installation of additional dependencies during runtime is not possible. The solution must be reproducible, resilient to environmental limitations, and run correctly in the secureintelligent/acp Docker container.

 

The evaluation is conducted on 15 independent tasks using binary scoring: each task gets a score of 1 (solved) or 0 (not solved). The pool includes scenarios for code vulnerability detection, forensics, security flaw fixes in a SWE-bench-like format and CTF-based task classes. Each problem has its own time and token limits, so participants must optimize not only accuracy but also cost/reasoning speed. Leaderboard position is determined primarily by the number of solved tasks; if the results are equal, the agent that completes the tasks faster and more efficiently uses tokens is ranked higher. The goal of the competition is to develop practically useful approaches in order to build information security agents that effectively operate on small local LLMs in closed-loop environments.

Data
Main files:

agent/ - folder with the participant's agent template/contract (what and how is launched at runtime).
agent/run.sh is the agent's main entrypoint; it is what the runner calls with the task text.
agent/agent.py - Harbor wrapper for MyInstalledAgent, standard integration interface.
agent/local_agent.py - an example of a local implementation of agent logic (can be replaced with your own).
sample_submission.zip - an example of what a participant's submission archive should look like (a .zip file with the required structure).
local_task/ - a set of local sample tasks for development/debugging (not a final closed benchmark).
The repository for local tests is available at: https://github.com/SecureIntelligent/UniversalAgenticCompetitionPublic
Requirements for the solution format
submission.zip archive weighing up to 10 MB:

there must be a run.sh script inside to launch the agent.
Solution evaluation criteria
Each task is assessed binary:

1 point – the solution to the task is automatically checked and counted;
0 points – the solution was not accepted by the automatic check.
 The final score is calculated as the proportion of correctly solved tasks:
 

The final score = (sum of scores for all tasks) / (total number of tasks). That is, the final result is the proportion of tasks the agent solved correctly. All participant solutions are evaluated on a single closed set of tasks the same for all participants.

The results for this task during the main stage will not be taken into account when determining the winner of the competition following the final and online defense.

0 points are awarded for solving a task when:

The agent gets 0 points for the task in all cases where the automatic check does not confirm the correct solution, including (but not limited to):

the code was not run;
the code ran but produced an incorrect result;
execution was stopped by timeout;
An error/failure occurred during the agent's operation (process crash, exception, etc.).
In all of the above cases, the task is considered unsolved and 0 points are awarded for it.
 

Ranking rules for equal results

If several participants have scored the same final score, an additional ranking is applied based on performance efficiency:

the solution with the smaller number of used LLM tokens is placed higher; the number of used tokens is understood as the total number of input and output tokens of all requests to the local LLM in the process of solving all tasks in the set;
If the number of tokens is the same, the solution with the shorter execution time is ranked higher. Execution time is calculated as the total time it takes to solve all tasks in the pool, from agent startup to solution completion.
Thus, with equal accuracy, the more economical and faster agent gets the advantage.

Restrictions and requirements
The agent must run without internet access within the `secureintelligent/acp` docker environment, otherwise the solution is scored 0.
Review system and decision processing calendar
Dear participants!

Please note that solutions to this task are verified using the checkpoint principle. Automatic recalculation of results and instant leaderboard updates are not provided.

All solutions submitted before the next checkpoint are uploaded and evaluated as a set of solutions – one latest solution per team at the time of upload. Until tthe solutions are uploaded to the next checkpoint, participants may update their solution an unlimited number of times. The results of the evaluation are published on the leaderboard according to the following schedule:
 

Checkpoint

Uploading your solutions

Publishing results on the leaderboard

CP No. 1

July 27 at 12:00 (Moscow time)

until August 3, 23:59 (Moscow time)

CP No. 2

August 11 at 12:00 (Moscow time)

until August 17, 23:59 (Moscow time)

CP No. 3

August 24 at 12:00 (Moscow time)

until August 27, 23:59 (Moscow time)

CP No. 4

August 31 at 12:00 (Moscow time)

until September 3, 23:59 (Moscow time)

CP No. 5

September 7 at 12:00 (Moscow time)

until September 10, 23:59 (Moscow time)

CP No. 6

September 14 at 12:00 (Moscow time)

until September 17, 23:59 (Moscow time)

CP No. 7

September 18 at 12:00 (Moscow time)

until September 22, 23:59 (Moscow time)

 

Please take this schedule into account when planning your submissions and tracking your results on the leaderboard.

 

Regardless of the deadline for submitting your solution and publishing your results on the leaderboard, you can evaluate your solution yourself using the local testing repository at the following link:

https://github.com/SecureIntelligent/UniversalAgenticCompetitionPublic