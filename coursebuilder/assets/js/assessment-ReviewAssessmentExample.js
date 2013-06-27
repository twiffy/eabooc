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
  preamble: 'Your answers will be reviewed by five of your peers. ',

  questionsList: [
    {questionHTML: 'Provide a short summary of your lesson and context from the first assignment for the benefit of your classmates and the instructor (so they don’t have to look back).  You should also add any new insights about the lesson that have emerged as you have thought about it more in the previous assignment(s).',
	 multiLine: true,
     correctAnswerRegex: /.*/i
    },

    {questionHTML: '<strong>Create two selected-response items</strong>.  Read about the four item types and decide which is most useful and relevant to you.  Make examples of two of the four.  Obviously the items should be related to your instructional activity and your standards, but it does not have to be perfectly aligned.  Remember that the main goal is just trying to apply the general item writing commandments and the specific guidelines for each of the item types',
     multiLine: true,
     correctAnswerRegex: /.*/i
	},

    {questionHTML: '<strong>Summarize three or more relevant big ideas about selected-response items.</strong> Review the What Teacher Need to Know…. section and the chapter summary at the end.  List three or more big ideas that are most relevant to you. Your summary of the ideas should make it clear why they are the most relevant to you. These are the BIG ideas of the chapter, not the specific guidelines used above.',
     multiLine: true,
     correctAnswerRegex: /.*/i
    },
  ],

  // The assessmentName key is deprecated in v1.3 of Course Builder, and no
  // longer used. The assessment name should be set in the unit.csv file or via
  // the course editor interface.
  assessmentName: 'ReviewAssessmentExample',
  checkAnswers: false
}
