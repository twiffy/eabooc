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

  '<h1>Unit 7 (Chapter 12) Practice Test</h1>',

  '<h2>Question 1</h2>',

  "<p>In 2-4 sentences, describe the difference between “assessment <em>of</em> learning” and “assessment <em>for</em> learning.”</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Often also called “summative assessment,” assessment *of* learning is when assessment is mainly seen as a way to figure out how much students have learned. Assessment *for* learning, however, is a way to figure out instructional effectiveness and make changes to classroom learning and teaching as needed. Assessment *for* learning is similar to and sometimes called “formative assessment.”",
    correctAnswerOutput: "bug",
    outputHeight: "100px"

  },



  '<h2>Question 2</h2>',
  "<p>Briefly describe the findings of the 1998 research review by Paul Black and Dylan Wiliam of classroom-assessment studies.</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "The main finding of the Black and Wiliam research study is that formative assessment does improve learning. Another significant finding is that formative assessment has not been found to have any negative effects to teaching and learning. Additionally, formative assessment works in a large variety of contexts. (You may have also written some of the other findings as well, these three are the most significant finds, though).",
    correctAnswerOutput: "bug",
    outputHeight: "100px"
  },


  '<h2>Question 3</h2>',
  "<p>What is/are the most important element(s) to implementing classroom Formative Assessment?</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "Most importantly, the use of assessment-elicited evidence to make adjustments. But also, the instructor’s willingness to make classroom changes is important.",
    correctAnswerOutput: "bug",
    outputHeight: "100px"
  },



  '<h2>Question 4</h2>',
  "<p>In your own words, write the four steps for building a learning progression.</p>",

  {
    questionType: 'freetext',
    correctAnswerRegex: /[]{1}/, // Never matches!
    incorrectAnswerOutput: "The following are the four steps written in Popham’s words. Check your own list against these steps to make sure yours has the same meaning.\nStep 1: Acquire a thorough understanding of the target curricular aim.\nStep 2: Identify all the requisite precursory subskills and bodies of enabling knowledge.\nStep 3: Determine the measurability of each preliminarily identified building block.\nStep 4: Arrange all the building blocks in an instructionally sensible sequence.",
    correctAnswerOutput: "bug",
    outputHeight: "120px"
  },


];

