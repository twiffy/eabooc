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


// Usage instructions: Create a single array variable named 'activity'. This
// represents explanatory text and one or more questions to present to the
// student. Each element in the array should itself be either
//
// -- a string containing a set of complete HTML elements. That is, if the
//    string contains an open HTML tag (such as <form>), it must also have the
//    corresponding close tag (such as </form>). You put the actual question
//    text in a string.
//
// -- a JavaScript object representing the answer information for a question.
//    That is, the object contains properties such as the type of question, a
//    regular expression indicating the correct answer, a string to show in
//    case of either correct or incorrect answers or to show when the student
//    asks for help. For more information on how to specify the object, please
//    see http://code.google.com/p/course-builder/wiki/CreateActivities.

//
// This is not "real" javascript.  The Python code must be able to parse it,
// and gives parse errors (not semantic errors) if you (e.g.) use different
// fields than it expects.
//

var activity = [

  '<p>These self-assessments are mainly intended for you to check your undersanding about the concepts covered on each unit. They do not affect your final grade.</p>',

  '<h1>Unit 8 (Chapter 13) Practice Test</h1>',

  '<h2>Question 1</h2>',

  "<p>In your own words and in 2-4 sentences, define the difference between <em>absolute</em> and <em>relative</em> terms.</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "An absolute score is the number of correct responses an individual got on a test whereas the relative score is the individual’s performance in relation to other other individuals. The absolute score allows us to infer what the individual can and cannot do and the relative score allows us to compare the individual to others in a particular group.",
    correctAnswerOutput: "bug",
    outputHeight: "100px"

  },



  '<h2>Question 2</h2>',
  "<p>In 2-4 sentences, explain what it means that a student has a percentile score of 72%. Be sure to define percentile and norm in your explanation.</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "A percentile compares a student to other students in a norm group that consists of a group of individuals who previously took the test. A score of 72% means that the student scored higher than the 72% of those in the norm group.",
    correctAnswerOutput: "bug",
    outputHeight: "100px"
  },


  '<h2>Question 3</h2>',
  "<p>In 2-4 sentences, explain what it means that a first grade student has a grade equivalent of 3.6 in reading.</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "The score of 3.6 demonstrates the first grader’s score along a continuum of development. The score means that the first grader scored as well on the reading skills that were tested as a student in the sixth month of third grade would score on those reading skills.\n\nNOTE: Remember that the score does NOT mean that the first grader should be promoted to third grade nor does it mean that the first grader can do third grade level work.",
    correctAnswerOutput: "bug",
    outputHeight: "100px"
  },



  '<h2>Question 4</h2>',
  "<p>A number of tests, such as the SAT, ACT, and the TOEFL, use scaled scores. In less than 4 sentences and in your own words, explain a scaled score.</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "In simple terms, a scaled score is when a raw score is converted to another, more interpretable score. This is especially useful when multiple forms of a test are used because the scaled score allows the scores on various forms to be compared to one another. It is important to note that the new scale is arbitrarily chosen.",
    correctAnswerOutput: "bug",
    outputHeight: "100px"
  },


];

