BACKGROUND_PROMPT = """Tell me 10 backgrounds in {theme} themed novels and scripts.

Each background should only include {component} behind literary works and no any other extra narratives. 

Each line starts with a serial number and a dot. 
"""


PROTAGONIST_PROMPT = """The following is the theme and background of a novel or script:

### Theme
{theme}

### Background
{background}

Based on the theme and background mentioned above, tell me 3 possible protagonists.
The protagonist is the main character portrayed in the narratives about their growth.
Each protagonist should only include a brief characterization, without specific names.
"""


PROTAGONIST_ANTAGONIST_PROMPT = """The following is the theme and background of a novel or script:

### Theme
{theme}

### Background
{background}

Based on the theme and background mentioned above, tell me 3 possible (protagonist, antagonist) pairs.
The protagonist is the main character portrayed in the narratives about their growth.
The main role of the antagonist is to create a conflict event with the protagonist to prevent it from achieving its goal.
Each pair should be presented in the format: protagonist: <a brief characterization>; antagonist: <a brief characterization>.
Please remember to use protagonist and antagonist without specific names appearing.
"""


PROTAGONIST_DEUTERAGONIST_PROMPT = """The following is the theme and background of a novel or script:

### Theme
{theme}

### Background
{background}

Based on the theme and background mentioned above, tell me 3 possible (protagonist, deuteragonist) pairs.
The protagonist is the main character portrayed in the narratives about their growth.
The main role of the deuteragonist is to collaborate with the protagonist to achieve its goal.
Each pair should be presented in the format: protagonist: <a brief characterization>; deuteragonist: <a brief characterization>.
Please remember to use protogonist and deuteragonist without specific names appearing.
"""


EVENT_PROMPT = """The following is the theme, background and persona of a novel or script:

### Theme
{theme}

### Background
{background}

### Persona
{persona}

Based on the theme, background and persona mentioned above, conceive two independent events that could run through the entire narrative context.
Please use a concise and coherent sentence to describe the entire event.
"""


ENDING_PROMPT = """The following is the theme, background, persona and main event of a novel or script:

### Theme
{theme}

### Background
{background}

### Persona
{persona}

## Event
{event}

Based on the theme, background, persona and event mentioned above, conceive an concretized ending.
Please use a concise and coherent sentence to describe the ending.
"""


TWIST_PROMPT = """The following is the theme, background, persona, main event and ending of a novel or script:

### Theme
{theme}

### Background
{background}

### Persona
{persona}

## Event
{event}

## Ending
{ending}

Based on the theme, background, persona, event and ending mentioned above, conceive a twist as an unique hook to connect the main event and ending.
Please use a concise and coherent sentence to describe the twist.
"""


SYNYHESIZE_PROMPT = """The following is the theme, background, persona, main event, final ending and twist of a novel or script:

### Theme
{theme}

### Background
{background}

### Persona
{persona}

## Event
{event}

## Ending
{ending}

## Twist
{twist}

Please combine the aforementioned elements of a novel or script into one compact, concise, and coherent sentence as a story premise.
"""


VERIFY_PROMPT = """Here is a story premise:

{premise}

Please help to verify:

1. Does it contain obvious inconsistencies. For example, the background, plot, and characters do not match

2. Does it contain obvious factual errors. For example, there were obvious historical errors and time span errors

If there are any errors mentioned above, please return Yes wrapped by `[[]]`, otherwise return No wrapped by `[[]]` without any other extra output.
"""


FASCINATION_SCORE_PROMPT = """Here is a story premise:

{premise}

Now let's give you a score from 0 to 100 to assess to its fascination.

Score 0 indicates that this premise is completely confused, while score 100 indicates that you really want to see the story created based on this premise.

Requirement: just provide a deterministic score and provide a concise and brief explanation, with a blank line between the two.

Score:"""


ORIGINALITY_SCORE_PROMPT = """Here is a story premise:

{premise}

Now let you give a score from 0 to 100 which represents your level of familiarity with it.

Score 0 indicates that you have seen the exact same premise, while score 100 indicates that you have never seen the same premise at all.

Your score should be based on the assumption that the candidate is at least a complete story premise. Otherwise, you should give a score 0.

Requirement: just provide a deterministic score and provide a concise and brief explanation, with a blank line between the two.

Score:"""


COMPLETENESS_SCORE_PROMPT = """Here is a story premise:

{premise}

Now let's give you a score from 0 to 100 which represents its completeness level.

Score 0 indicates that it lacks all elements , while score 100 indicates that it has all elements.

Requirement: just provide a deterministic score and provide a concise and brief explanation, with a blank line between the two.

Score:"""
