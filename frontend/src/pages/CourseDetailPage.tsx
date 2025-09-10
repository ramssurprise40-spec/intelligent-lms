import React from 'react';
import { useParams } from 'react-router-dom';

export default function CourseDetailPage() {
  const { courseId } = useParams();
  
  return (
    <div>
      <h1 className="text-3xl font-bold">Course Details</h1>
      <p className="mt-4 text-gray-600">Course ID: {courseId}</p>
    </div>
  );
}
