// Copyright 2012 Google Inc. All Rights Reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS-IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.


// When the assessment page loads, activity-generic.js will render the contents
// of the 'assessment' variable into the enclosing HTML webpage.

// For information on modifying this page, see
// https://code.google.com/p/course-builder/wiki/CreateAssessments.


var assessment = {
  // HTML to display at the start of the page
  preamble: '',

  // An ordered list of questions, with each question's type implicitly determined by the fields it possesses:
  //   choices              - multiple choice question (with exactly one correct answer)
  //   correctAnswerString  - case-insensitive string match
  //   correctAnswerRegex   - freetext regular expression match
  //   correctAnswerNumeric - freetext numeric match
  questionsList: [

    {questionHTML: "Which of the following statements most accurately reflects the relationship between students’ aptitude and their achievement?",
      choices: [
        'Both aptitude and achievement are equivalent to a traditional conception of intelligence.',
        correct('Whereas aptitude tends to reflect potential, achievement tends to reflect prior learning.'),
        'Actually, achievement is little more than an operationalization of aptitude.',
        'The level of a student’s aptitude can never exceed the level of the student’s achievement.',
      ],

    },


    {questionHTML: "If Mr. Higgins, a fourth-grade teacher, tries to evaluate his major exams by ascertaining the degree to which his test’s items are functioning in a similar manner, what kind of test-evaluative evidence is this?",
      choices: [
        'Stability reliability evidence',
        'Alternate-form reliability evidence',
        correct('Internal-consistency reliability evidence'),
        'None of the above',

      ],

    },


    {questionHTML: "Which of the following descriptions of validity is most accurate?",
      choices: [
        'Validity refers to the consistency with which a test measures whatever it is measuring.',
        'Validity describes the degree to which a test’s usage leads to appropriate consequences for students.',
        'Validity describes the legitimacy of the decision to which a test-based inference will be put.',
        correct('Validity refers to the accuracy of score-based interpretations about students.'),
      ],

    },


    {questionHTML: "Which of the following is a typical classroom teacher most likely to collect?",
      choices: [
        correct('Content-related evidence of validity'),
        'Predictive criterion-related evidence of validity',
        'Concurrent criterion-related evidence of validity',
        'Standard-error-of-measurement evidence',
      ],

    },


    {questionHTML: "Which of the following approaches to bias-elimination is it most reasonable to expect classroom teachers to use?",
      choices: [
        'Empirical approaches',
        correct('Judgmental approaches'),
        'Both empirical and judgmental approaches are equally reasonable for classroom teachers to use.',
        'Neither empirical nor judgmental approaches are reasonable for classroom teachers to use.',
      ],

    },


    {questionHTML: "As employed by most of today’s educators, to which of the following is the expression, “content standard” most equivalent?",
      choices: [
        'Performance standard',
        'Content validity',
        correct('Curricular goal'),
        'Curricular assessment',
      ],

    },


    {questionHTML: "Which of the following assertions is most accurate?",
      choices: [
        correct('Criterion-referenced score-based inferences are relative interpretations.'),
        'Norm-referenced score-based inferences are absolute interpretations.',
        'Norm-referenced score-based inferences and criterion-referenced score-based inferences are not essentially interchangeable.',
        'Norm-referenced score-based inferences are typically more useful to classroom teachers than criterion-referenced score-based inferences.',
      ],

    },


    {questionHTML: "What is the chief role of the National Assessment of Educational Progress (NAEP)?",
      choices: [
        'To compare the academic performances of U.S. students with those of students in other nations',
        'To promote more consistent curriculum targets in the 50 U.S. states',
        correct('To monitor U.S. students’ academic achievement over time'),
        'To satisfy the measurement requirements of any state whose officials wish to measure students’ mastery of specific content standards',
      ],

    },


    {questionHTML: "During recent years, when results of NAEP tests are contrasted with results of state accountability tests, which of the following statements best captures the relationship between those two sets of results?",
      choices: [
        'Students’ performances on NAEP and on state accountability tests are essentially equivalent.',
        correct('Students’ performances on a state’s tests are classified higher than those same students’ scores on NAEP.'),
        'Students’ performances on NAEP are typically better than those same students’ scores on their state’s accountability tests.',
        'Students in a state usually score better on NAEP than they do on their own state’s mathematics tests, but less well on their state’s reading tests than they do on NAEP reading tests.',
      ],

    },


    {questionHTML: "Which of the following is a general item-writing rule that should be followed in the writing of all items for classroom assessments?",
      choices: [
        'To challenge students adequately, use vocabulary terms slightly more advanced than required.',
        'If possible, provide clues for students to come up with correct answers even if those clues are not directly relevant to the knowledge and/or skill being assessed.',
        'Because stronger students will usually be able to discern the nature of the assessment tasks before them, directions about how students are to respond need not be specific or detailed.',
        correct('Attempt to employ syntax in test items that is well within the understanding levels of the students being assessed.'),
      ],

    },


    {questionHTML: "Which of the following is a recommended item-writing rule for the construction of binary-choice items?",
      choices: [
        'Include no more than two concepts in any one statement.',
        correct('Employ a roughly equal number of statements representing the two categories being tested.'),
        'If one category being assessed requires longer statements than the other category, be sure that the disparity in statement-length is constant.',
        'Employ relatively few double-negative statements and, if you do, be sure to emphasize with italics or bold-face type that a negative is involved.',
      ],

    },


    {questionHTML: "One of the important rules to be followed in creating multiple binary-choice items is that:",
      choices: [
        'Most items should mesh sensibly with a cluster’s stimulus material.',
        correct('Item clusters should be strikingly separated from one another.'),
        'The stimulus material for any cluster of items should contain a substantial amount of extraneous information.',
        'Multiple binary-choice items, to avoid confusion, should never be included in a test already containing binary-choice items.',
      ],

    },


    {questionHTML: "Which of the following is an item-writing guideline for the construction of multiple-choice items?",
      choices: [
        'Generally, especially with young children, the stem should consist of an incomplete statement rather than direct question.',
        correct('Don’t ever use “all-of-the-above” alternatives, but use a “none-of-the-above” alternative to increase an item’s difficulty.'),
        'Typically, make the later answer options, such as “C” and “D,” the correct answers.',
        'Supply clues to the correct answer by using alternatives of dissimilar lengths.',
      ],

    },


    {questionHTML: "Which of the following rules is often recommended for the generation of matching items?",
      choices: [
        'Order all of the premises alphabetically, but arrange the responses in an unpredictable manner.',
        'Place the premises for an item on one page, then put most of the responses for that item on the following page.',
        'Ideally, both the premises and the responses should represent fundamentally heterogeneous lists.',
        correct('Employ relatively brief lists, placing the shorter words or phrases at the right.'),
      ],

    },


    {questionHTML: "One of the following rules for the construction of essay items is accurate.  The other three rules are not.  Which is the correct rule?",
      choices: [
        'Force students to allocate their time judiciously by never indicating how much time should be expended on a particular item.',
        'Give students an opportunity to match their achievement levels with the essay test by allowing them to choose, from optional items, those they will answer.',
        correct('Construct all essay items so the student’s task for each item is unambiguously described.'),
        'Judge the quality of a given set of essay items by seeing how accurately a tryout group of students can comprehend what responses are sought.',
      ],

    },


    {questionHTML: "Which of the rules given below accurately reflects one of the guidelines generally given to classroom teachers who must score students’ responses to essay items?",
      choices: [
        'Score an entire test, that is, the student’s responses to all items, before going on to the next student’s test.',
        'After all answers to all essay items have been scored, decide how much weight you should give—if any—to such factors as spelling, punctuation, and grammar.',
        'Attempt to apply Bloom’s Cognitive Taxonomy to the scoring process.',
        correct('Prepare a tentative scoring key prior to judging any student’s response—being ready to modify it if this seems warranted during the scoring.'),
      ],

    },


    {questionHTML: "Which of the following is <i>not</i> an element typically embodied in performance tests?",
      choices: [
        'Judgmental appraisal of students’ responses',
        'Prespecified evaluative criteria for judging students’ responses',
        'Multiple evaluative criteria',
        correct('A direct link to a preexisting content standard'),
      ],

    },


    {questionHTML: "A <i>rubric</i> is a scoring guide to be employed in judging students’ responses to constructed-response assessments such as a performance test.  Which one of the following elements is the <strong>least</strong> necessary feature of a properly constructed rubric?",
      choices: [
        'An identification of the evaluative criteria to be used in appraising a student’s response',
        correct('A designation of a performance standard required for skill-mastery'),
        'Descriptions of different quality levels associated with each evaluative criterion',
        'An indication of whether a holistic or analytic scoring approach is to be used',
      ],

    },


    {questionHTML: "Which of the following is not a key step that a classroom teacher needs to take in getting underway with a portfolio assessment program?",
      choices: [
        'Decide on the kinds of work samples to collect.',
        correct('Decide which students should be involved in the portfolio assessment program.'),
        'Require students to evaluate continually their own portfolio products.',
        'Schedule and conduct a meaningful number of portfolio conferences.',
      ],

    },


    {questionHTML: "Which of the following, from a classroom teacher’s perspective, is probably the most serious drawback of portfolio assessment?",
      choices: [
        'Parents’ negative reactions to portfolio assessment',
        'Students’ negative reactions to portfolio assessment',
        correct('Portfolio assessment’s time-demands on teachers'),
        'The excessive attention given to portfolio assessment by educational policymakers',
      ],

    },


    {questionHTML: "Which one of the following statements regarding the improvement of classroom assessments is <strong>not</strong> accurate?",
      choices: [
        'Classroom teachers can employ judgmental improvement procedures, empirical procedures, or both.',
        'For selected-response tests, especially multiple-choice items, distractor analyses can prove useful in item-improvement.',
        'Performance-based approaches to item improvement usually are different for tests aimed at criterion-referenced inferences than for those aimed at norm-referenced inferences.',
        correct('Students’ reactions to test items should play little or no role in item improvement.'),
      ],

    },


    {questionHTML: "Which of the following questions is not an element in a research-supported conception of formative assessment?",
      choices: [
        'Formative assessment is a process, not a test.',
        correct('Formative assessment calls for the use of assessment-elicited evidence in making adjustment decisions.'),
        'Formative assessment should be used only by teachers to adjust their ongoing instructional activities.',
        'Formative assessment must be carefully planned.',
      ],

    },


    {questionHTML: "Which of the following is generally conceded to be a key component of formative assessment?",
      choices: [
        'Data obtained via standardized achievement tests',
        'A heavy emphasis on using students’ classroom test results as a dominant factor in determining students’ grades',
        correct('The framework provided by a learning progression’s building blocks'),
        'A teacher’s exclusive reliance on the collection of data using constructed-response tests.',
      ],

    },


    {questionHTML: "Which of the following is an <i>instructionally</i> beneficial rubric?",
      choices: [
        'A task-specific rubric',
        'A hypergeneral rubric',
        correct('A skill-focused rubric'),
        'None of the above',
      ],

    },


    {questionHTML: "Which of the following rules is <i>not</i> one that is recommended when creating a scoring rubric that will have a positive impact on classroom instruction?",
      choices: [
        'Make certain the skill to be assessed is truly significant.',
        'Be sure that all of the rubric’s evaluative criteria can be addressed instructionally by teachers.',
        correct('Employ as many evaluative criteria as possible to judge major aspects of students’ responses.'),
        'Provide a terse label for each of the rubric’s evaluative criteria.',
      ],

    },


    {questionHTML: "Which of the following is the <i>most</i> often misinterpreted score-interpretation indicator used with standardized tests?",
      choices: [
        'Raw score',
        'Percentile',
        'Stanine',
        correct('Grade-equivalent score'),
      ],

    },


    {questionHTML: "Consider the following statements regarding test-preparation.  Which one is <i>not accurate</i>?",
      choices: [
        'Appropriate test-preparation will simultaneously improve students’ test scores as well as students’ mastery of the knowledge and/or skills represented by the test.',
        'If relatively brief, generalized test-taking preparation focused on such skills as how to manage one’s time during test-taking is quite appropriate.',
        correct('If teachers simultaneously direct their instruction toward a test’s specific items and the curricular aim on which the test is based, this constitutes appropriate test preparation.'),
        'If teachers adhere to the ethical norms of the education profession while preparing their students, this is an important ingredient in appropriate test-preparation activities.',
      ],

    },


    {questionHTML: "Which statement best characterized the current use of formative assessment in the United States?",
      choices: [
        'Most teachers now employ the formative-assessment process in their classes.',
        correct('Although research-supported, formative assessment is not widely used.'),
        'Only a five-strategies approach to formative assessment is often encountered.',
        'A four-levels approach to formative assessment is used in the lower grades.',
      ],

    },


    {questionHTML: "Which of the following is <i>not</i> a reason that should dissuade policymakers from evaluating educational quality on the basis of students’ scores on certain educational achievement tests?",
      choices: [
        'There are often substantial mismatches between the content covered on some of these tests and local curricular emphases.',
        correct('Substantial gaps between minority and majority students’ performance on most accountability tests will rarely be found.'),
        'There is a technical tendency to remove from such tests items covering important, teacher-stressed knowledge and skills.',
        'It is difficult to tell from such tests how much of a student’s test performance is due to what was taught in school rather than to students’ socioeconomic status or inherited academic aptitudes.',
      ],

    },


    {questionHTML: "Which of the following statements about goal-attainment grading is <i>most</i> defensible?",
      choices: [
        '“Because students’ effort plays such a pivotal role in a student’s ultimate learning, all goal-attainment grading must include a provision for incorporating students’ levels of effort.”',
        '“Given its focus on students’ mastery of curricular-targets, goal-attainment grading essentially precludes the possibility of teachers’ measuring students’ affective dispositions.”',
        '“Because of the centrality of curricular aims in any goal-attainment conception of grading, the curricular targets being sought should be carefully described to students’ parents and to students themselves at grading time.”',
        correct('“If a teacher can collect defensible assessment evidence of a student’s mastery of the teacher’s designated curricular aims, then this evidence should be the only basis for goal-attainment grading.”'),
      ],

    },

    ],

  // The assessmentName key is deprecated in v1.3 of Course Builder, and no
  // longer used. The assessment name should be set in the unit.csv file or via
  // the course editor interface.
  assessmentName: 'Final', // unique name submitted along with all of the answers

  checkAnswers: false     // render a "Check your Answers" button to allow students to check answers prior to submitting?
}

