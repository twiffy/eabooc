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

    {questionHTML: 'Which of the following statements represents the significant difference between a “content standard” and a “performance standard”?',
      choices: [
        'The content standard represents what educators what students to do and the performance standard represents what educators want students to learn.',
        'The performance standard represents the academic knowledge and the content standards represent the achieved proficiency.',
        'The content standard represents the measurable skills and the performance standards represents behaviors that can be described only.',
        correct('The content standard represents what educators want students to learn academically and the performance standard represents the desired level of proficiency educators want to students to achieve.'),],

    },

  // The assessmentName key is deprecated in v1.3 of Course Builder, and no
  // longer used. The assessment name should be set in the unit.csv file or via
  // the course editor interface.
  assessmentName: 'Principles', // unique name submitted along with all of the answers

  checkAnswers: false     // render a "Check your Answers" button to allow students to check answers prior to submitting?
}

