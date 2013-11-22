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

    {
	    questionHTML: "Parents who want their children to score high on standardized achievement tests would be most happy if their child earned which of the following percentiles?",
      choices: [
        '50th',
        '2nd',
        correct('99th'),

      ],
    },

    {
	    questionHTML: "Which of the following score-interpretation options is most <i>readily interpretable?</i>",
      choices: [
        correct('Percentiles'),
        'NCEs',
        'Grade equivalents',

      ],
    },

    {
	    questionHTML: "Which of the following score-interpretation options is especially useful in equalizing the disparate difficulty levels of different test forms?",
      choices: [
        'Percentiles',
        'Grade equivalents',
        correct('Scale scores'),

      ],
    },

    {
	    questionHTML: "Which of the following score-interpretation options is <i>most often misunderstood?</i>",
      choices: [
        'Stanines',
        correct('Grade equivalents'),
        'Percentiles',

      ],
    },

    {
	    questionHTML: "Which of the following score-interpretation indices were initially introduced to permit amalgamation of students’ scores on different standardized tests?",
      choices: [
        correct('Normal curve equivalents'),
        'Stanines',
        'Grade equivalents',

      ],
    },

    {
	    questionHTML: "True or False. The heart of the <i>Professional Ethics Guideline</i> is that teachers should not prepare students for tests in a way that violates universal canons of fundamental morality.",
      choices: [
        'True',
        correct('False'),

      ],
    },

    {
	    questionHTML: "True or False. The essence of the <i>Educational Defensibility Guideline</i> is that a suitable test-preparation practice will boost students’ mastery on both a curricular aim’s domain knowledge and/or skill as well as the test representing that curricular aim.",
      choices: [
        correct('True'),
        'False',

      ],
    },

    {
	    questionHTML: "True or False. Generalized test-taking preparation, if not excessively lengthy, represents an appropriate way to ready students for a high-stakes test.",
      choices: [
        correct('True'),
        'False',

      ],
    },

    {
	    questionHTML: "True or False. Current-form preparation, that is, special instruction based on an existing form of a test, can be appropriate in some situations.",
      choices: [
        'True',
        correct('False'),

      ],
    },

    {
	    questionHTML: "True or False. Most standardized achievement tests are accompanied by fairly explicit descriptions of what is being measured, such descriptions being sufficiently clear for most teachers’ instructional planning purposes.",
      choices: [
        'True',
        correct('False'),

      ],
    },

    {
	    questionHTML: "Which of the following is NOT a factor to take into account when structuring an evaluative strategy for your classroom?",
      choices: [
        'Evidence pertaining to any positive or negative side effects.',
        'Assessment evidence collected via accountability tests.',
        correct('Evidence pertaining to assessments taken previous to the current level.'),
        'Assessment evidence collected via classroom assessments.',

      ],
    },

    {
	    questionHTML: "Which of the following is a key strength of the pretest versus posttest model for determining instructional impact?",
      choices: [
        'Testing a student before and after instruction provides more data than testing just once',
        correct('Testing a student before and after instruction ensures that you measure how much the teaching impacted changes in performance.'),
        'Testing a student before and after instruction accounts for factors such as the the “dissimilar students” problem.',
        'Testing a student before and after instruction accounts for any student growth that can happen by chance alone.',

      ],
    },

    {
	    questionHTML: "What is one reason that the “split-and-switch” design can provide better evidence of a teacher’s instructional effectiveness than simply pretesting and posttesting?",
      choices: [
        correct('It controls for the testing effect whereby the pretest tells students what will be on the posttest'),
        'It provides the instructor with evidence of instructional effectiveness regardless of the size of the class.',
        'It provides the instructor with evidence to judge instructional effectiveness in the form of pretest and posttest grades.',
        'None of the above.',

      ],
    },

    {
	    questionHTML: "Which of the following statements does NOT represent instructional sensitivity?",
      choices: [
        'The focus of instructional sensitivity is on instructional quality--which is the amount of instruction directed toward student achievement on a skill.',
        'An instructionally sensitive test will accurately distinguish between effectively and ineffectively taught students.',
        'The focus of instructional sensitivity is on the degree to which test performance measures the quality of instruction directed toward students’ mastery of a skill.',
        correct('An instructionally sensitive test will be sensitive to the instruction provided to promote student’s mastery on what is being assessed.'),
      ],
    },

    {
      questionHTML: "Which of the following represents an accurate definition of Value-Added Model (VAM)?",
      choices: [
        "An approach to teacher evaluation that measures the teacher's contribution in a given year by comparing the current standardized test scores of all the students in that class to the scores of the students in the same class last year.",
        correct('An approach to teacher evaluation that represents a statistical strategy to increase the accuracy of estimates of achievement gains of each student from one year to the next.'),
        'An approach to teacher evaluation that examines the effect a teachers has on student growth by examining various classroom assessments within a given year.',
        'None of the above.',


        ],
    },


    {
      questionHTML: "Indicate whether the following statement <i>Appropriately</i> or <i>Inappropriately</i> represents a goal-attainment approach to grading: “Goal-attainment grading emphasizes a teacher’s communicating information to students and their parents about students’ goal-attainment.”",
      choices: [
        correct('Appropriately'),
        'Inappropriately',
      ],
    },

    {
      questionHTML: "Indicate whether the following statement <i>Appropriately</i> or <i>Inappropriately</i> represents a goal-attainment approach to grading: “Genuine goal-attainment grading should be based <i>exclusively</i> on a student’s status with respect to the mastery of curricular aims.”",
      choices: [
        correct('Appropriately'),
        'Inappropriately',

      ],
    },

    {
      questionHTML: "Indicate whether the following statement <i>Appropriately</i> or <i>Inappropriately</i> represents a goal-attainment approach to grading: “All assessment-based evidence related to a student’s mastery of the teacher’s designated curricular aims should be weighted identically when goal-attainment graders arrive at students’ grades.”",
      choices: [
        'Appropriately',
        correct('Inappropriately'),

      ],
    },

    {
      questionHTML: "Indicate whether the following statement <i>Appropriately</i> or <i>Inappropriately</i> represents a goal-attainment approach to grading: “After clarifying curricular aims to students and their parents, a goal-attainment grader should identify the evidence by which a student’s attainment of goals will be determined.”",
      choices: [
        correct('Appropriately'),
        'Inappropriately',

      ],
    },

    {
      questionHTML: "Indicate whether the following statement Appropriately or Inappropriately represents a goal-attainment approach to grading: “For goal-attainment grading to succeed, especially when used with standards-based report cards, it will often be necessary to meaningfully reduce the number of grade-relevant goals via stringent prioritization.”",
      choices: [
        correct('Appropriately'),
        'Inappropriately',

      ],
    }

  ],

  // The assessmentName key is deprecated in v1.3 of Course Builder, and no
  // longer used. The assessment name should be set in the unit.csv file or via
  // the course editor interface.
  assessmentName: 'Policies', // unique name submitted along with all of the answers

  checkAnswers: false     // render a "Check your Answers" button to allow students to check answers prior to submitting?
}

