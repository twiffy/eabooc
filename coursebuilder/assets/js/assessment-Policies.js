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

    {questionHTML: "A commercial testing company has developed a brand new test intended to measure the mathematics skills of students who possess limited English proficiency.  Because there are three different forms of the test at each of six grade levels, and teachers are encouraged to use all three forms during the year, the sales representatives of the company are demanding reliability evidence (from technical personnel) that will best help them market the new test. What kind of reliability evidence seems most useful in this situation?",
      choices: [
        'Stability',
      correct('Alternate-Forms'),
      'Internal Consistency',
      ],

    },

    {questionHTML: "Of the following options, which one is—by far—the most integral to the implementation of formative assessment in a classroom?",
      choices: [
        'A teacher’s willingness to try new procedures in class',
        correct('Use of assessment-elicited evidence to make adjustments'),
        'Teachers’ willingness to refrain from grading most of their students’ exams',
        'Teachers’ use of a variety of both selected-response and constructed-response items',
        ],
    }],

  // The assessmentName key is deprecated in v1.3 of Course Builder, and no
  // longer used. The assessment name should be set in the unit.csv file or via
  // the course editor interface.
  assessmentName: 'Policies', // unique name submitted along with all of the answers

  checkAnswers: false     // render a "Check your Answers" button to allow students to check answers prior to submitting?
}

