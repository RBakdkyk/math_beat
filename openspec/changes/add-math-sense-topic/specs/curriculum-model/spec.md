## ADDED Requirements

### Requirement: Math-sense enrichment topic
The curriculum module SHALL define a `math-sense` topic, grounded in the kita4 number-sense and estimation strands (not a named Ministry subtopic, same category as `arithmetic-sequences`). Its generator SHALL vary internally among three question shapes: relational fill-in (e.g. "18×5=70 → 18×50=?"), parity-without-computing (e.g. "is 235+387 even or odd — without computing?"), and estimate-and-judge (e.g. "is 35×42 greater than 1000? reason without computing exactly"). Parameters SHALL be generated at runtime from rules, not enumerated lists, consistent with every other topic.

#### Scenario: Math-sense question generated deterministically
- **WHEN** a math-sense question is requested at any difficulty
- **THEN** Python randomly picks one of the three question shapes, generates valid parameters, and computes the answer without calling Claude

#### Scenario: Each shape produces a valid signature
- **WHEN** a math-sense question of any shape is generated
- **THEN** it carries a unique signature following the `"{type}:{params}"` convention, distinguishable by shape
