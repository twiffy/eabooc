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

  '<h1>Unit 10 (Chapter 15) Practice Test</h1>',

  '<h2>Question 1</h2>',

  "<p>Although many people use the terms “grading” and “evaluation” as though the two word are synonymous, what is the technical difference between these two terms?</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Evaluation deals with the determination of a teacher’s instructional effectiveness; grading deals with letting students know how well they are performing.",
    correctAnswerOutput: "bug",
    outputHeight: "100px"

  },



  '<h2>Question 2</h2>',
  "<p>It is said that one reason students’ scores on educational accountability tests should not be used to evaluate instruction is there is a “teaching-testing mismatch.”  What does this mean?</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Teaching-testing mismatches signify that a substantial amount of the content contained in the test’s items may not have been taught—or may not even supposed to have been taught.",
    correctAnswerOutput: "bug",
    outputHeight: "100px"
  },


  '<h2>Question 3</h2>',
  "<p>What does it mean when the use of traditional standardized achievement tests is rejected because of these tests’ “technical tendency to exclude items covering important content?”</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "In order to create a suitable score-spread among test-takers, items with high p values are typically not included in such tests or are subsequently removed at test-revision time.  Yet items on which students perform well often cover the content teachers thought important enough to stress.  The better that students do on an item, the less likely the items covering important, teacher-stressed content will be found on a certain educational accountability tests.",
    correctAnswerOutput: "bug",
    outputHeight: "120px"
  },



  '<h2>Question 4</h2>',
  "<p>What is meant by “instructional sensitivity”?</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Instructional sensitivity is the degree to which students’ performances on a test accurately reflect the quality of instruction specifically provided to promote students’ mastery of what is being assessed.",
    correctAnswerOutput: "bug",
    outputHeight: "100px"
  },


  '<h2>Question 5</h2>',
  "<p>Optional Question: The following question pertains to K-12 education in the United States. It is helpful for anyone teaching students at any level in the US or preparing students for education in the US to understand the role the federal government plays in education.</p>",

  "<p>Why is test-based teacher evaluation consonant with federal insistence that student growth constitute “a significant factor” in the evaluation of teachers?</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "The essence of test-based teacher evaluation is to make certain that students’ test scores—reflecting student growth—constitute a dominant determiner of judgments reached about a teacher’s quality.",
    correctAnswerOutput: "bug",
    outputHeight: "100px"
  },

];

