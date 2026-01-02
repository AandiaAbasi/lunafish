/**
 * Practice Service
 * API calls for practice exercises, exams, and results
 */

import axios, { AxiosError } from 'axios';
import { uri } from './URL';
import {
  CreateFieldRequest,
  Field,
  CreateExamRequest,
  Exam,
  ExamResult,
  ExamAttemptDetail,
  ApiResponse,
  PaginatedResponse,
  Fields,
} from '@/src/types/practiceType';

const API_BASE = uri;
const PRACTICE_API = `${API_BASE}/exercise`;

// ==================== Field (Question) Service ====================

/**
 * Create a new field/question
 * POST /api/exercise/field/create/
 */
export const createField = async (
  token: string,
  fieldData: CreateFieldRequest,
  files?: {
    image_path?: string;
    audio_path?: string;
    video_path?: string;
  }
): Promise<Field> => {
  try {
    // Build FormData for multipart/form-data submission
    const formData = new FormData();

    // Add all field data as JSON string or individual fields
    formData.append('title', fieldData.title);
    formData.append('type', fieldData.type);
    formData.append('is_required', String(fieldData.is_required || 1));
    formData.append('sort', String(fieldData.sort || 0));
    
    if (fieldData.guide) formData.append('guide', fieldData.guide);
    if (fieldData.des) formData.append('des', fieldData.des);
    if (fieldData.correct_answer) formData.append('correct_answer', fieldData.correct_answer);
    
    // Add details array - use form field notation for multipart/form-data
    // Backend validates that input types must have details with correct_answer
    if (fieldData.details && fieldData.details.length > 0) {
      console.log('📋 Sending details array:', fieldData.details);
      
      // Send each detail as individual form fields using array notation
      fieldData.details.forEach((detail, index) => {
        console.log(`  ✓ details[${index}][title] = "${detail.title}"`);
        formData.append(`details[${index}][title]`, detail.title);
        
        console.log(`  ✓ details[${index}][sort] = "${detail.sort || index}"`);
        formData.append(`details[${index}][sort]`, String(detail.sort || index));
        
        // For checkbox/radioButton types
        if ('is_correct' in detail && detail.is_correct !== undefined) {
          console.log(`  ✓ details[${index}][is_correct] = "${detail.is_correct}"`);
          formData.append(`details[${index}][is_correct]`, String(detail.is_correct));
        }
        
        // For input types - send correct_answer
        if ('correct_answer' in detail && (detail as any).correct_answer) {
          console.log(`  ✓ details[${index}][correct_answer] = "${(detail as any).correct_answer}"`);
          formData.append(`details[${index}][correct_answer]`, (detail as any).correct_answer);
        }
      });
    } else if (fieldData.type === 'input') {
      // For input types without details, this should not happen due to frontend validation
      console.warn('⚠️ Input type with no details - this should not happen');
    }

    // Add file uploads
    if (files?.image_path) {
      const filename = files.image_path.split('/').pop() || 'image.jpg';
      const match = /\.(\w+)$/.exec(filename);
      const extension = match?.[1]?.toLowerCase() || 'jpg';
      let mimeType = 'image/jpeg';
      if (extension === 'png') mimeType = 'image/png';
      else if (extension === 'gif') mimeType = 'image/gif';
      else if (extension === 'webp') mimeType = 'image/webp';

      formData.append('image_path', {
        uri: files.image_path,
        name: filename,
        type: mimeType,
      } as any);
    }

    if (files?.audio_path) {
      const filename = files.audio_path.split('/').pop() || 'audio.mp3';
      const match = /\.(\w+)$/.exec(filename);
      const extension = match?.[1]?.toLowerCase() || 'mp3';
      let mimeType = 'audio/mpeg';
      if (extension === 'wav') mimeType = 'audio/wav';
      else if (extension === 'm4a') mimeType = 'audio/mp4';
      else if (extension === 'aac') mimeType = 'audio/aac';
      else if (extension === 'ogg') mimeType = 'audio/ogg';
      else if (extension === 'flac') mimeType = 'audio/flac';

      formData.append('audio_path', {
        uri: files.audio_path,
        name: filename,
        type: mimeType,
      } as any);
    }

    if (files?.video_path) {
      const filename = files.video_path.split('/').pop() || 'video.mp4';
      const match = /\.(\w+)$/.exec(filename);
      const extension = match?.[1]?.toLowerCase() || 'mp4';
      let mimeType = 'video/mp4';
      if (extension === 'mov') mimeType = 'video/quicktime';
      else if (extension === 'avi') mimeType = 'video/x-msvideo';
      else if (extension === 'mkv') mimeType = 'video/x-matroska';
      else if (extension === 'webm') mimeType = 'video/webm';

      formData.append('video_path', {
        uri: files.video_path,
        name: filename,
        type: mimeType,
      } as any);
    }
    
    // Log FormData contents for debugging (FormData doesn't log well directly)
    console.log('📤 FormData being sent:');
    console.log('  title:', formData.get('title'));
    console.log('  type:', formData.get('type'));
    console.log('  is_required:', formData.get('is_required'));
    console.log('  sort:', formData.get('sort'));
    
    // Check for details in form array notation
    const detailKeys = Array.from((formData as any)._parts || [])
      .filter(([key]: any) => key.startsWith('details['))
      .map(([key]: any) => key);
    console.log(`  Found ${detailKeys.length} detail keys:`, detailKeys.slice(0, 5));

    const response = await axios.post<ApiResponse<Field>>(
      `${PRACTICE_API}/field/create/`,
      formData,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    if (response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to create field');
  } catch (error) {
    const apiError = error as AxiosError<ApiResponse<Field>>;
    console.log('====================================');
    console.log('API Error:', apiError.response?.data);
    console.log('====================================');
    const message =
      apiError.response?.data?.error ||
      apiError.response?.data?.message ||
      'Failed to create question';
    throw new Error(message);
  }
};

// ==================== Exam Service ====================

/**
 * Create a new exam (assign questions to class/subject)
 * POST /api/exercise/exam/create/
 */
export const createExam = async (
  token: string,
  examData: CreateExamRequest
): Promise<Exam> => {
  try {
    const response = await axios.post<ApiResponse<Exam>>(
      `${PRACTICE_API}/exam/create/`,
      examData,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      }
    );

    if (response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to create exam');
  } catch (error) {
    const apiError = error as AxiosError<ApiResponse<Exam>>;
    const message =
      apiError.response?.data?.error ||
      apiError.response?.data?.message ||
      'Failed to create exam';
    throw new Error(message);
  }
};

/**
 * Get exam questions for a subject/class
 * GET /api/exercise/exam/<subject_id>/
 */
export const getExam = async (
  token: string,
  subjectId: number
): Promise<Exam> => {
  try {
    const response = await axios.get<Exam>(
      `${PRACTICE_API}/exam/${subjectId}/`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  } catch (error) {
    const apiError = error as AxiosError<ApiResponse<Exam>>;
    const message =
      apiError.response?.data?.error ||
      apiError.response?.data?.message ||
      'Failed to fetch exam';
    throw new Error(message);
  }
};

// ==================== Results Service ====================

/**
 * Get all exam results (attempts) for teacher or student
 * GET /api/exercise/results/
 */
export const getExamResults = async (
  token: string,
  filters?: {
    subjectId?: number;
    page?: number;
    pageSize?: number;
  }
): Promise<PaginatedResponse<ExamResult>> => {
  try {
    const params: Record<string, any> = {
      page: filters?.page || 1,
      page_size: filters?.pageSize || 20,
    };

    if (filters?.subjectId) {
      params.subject_id = filters.subjectId;
    }

    const response = await axios.get<PaginatedResponse<ExamResult>>(
      `${PRACTICE_API}/results/`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        params,
      }
    );

    return response.data;
  } catch (error) {
    const apiError = error as AxiosError<PaginatedResponse<ExamResult>>;
    throw new Error(
      apiError.response?.data?.count !== undefined
        ? 'Failed to fetch results'
        : 'Failed to fetch exam results'
    );
  }
};

/**
 * Get detailed results for a specific exam attempt
 * GET /api/exercise/results/<attempt_id>/
 */
export const getExamAttemptDetail = async (
  token: string,
  attemptId: number
): Promise<ExamAttemptDetail> => {
  try {
    const response = await axios.get<ExamAttemptDetail>(
      `${PRACTICE_API}/results/${attemptId}/`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    return response.data;
  } catch (error) {
    const apiError = error as AxiosError<ApiResponse<ExamAttemptDetail>>;
    const message =
      apiError.response?.data?.error ||
      apiError.response?.data?.message ||
      'Failed to fetch attempt details';
    throw new Error(message);
  }
};

// ==================== Error Handling Utilities ====================

/**
 * Parse API error and return user-friendly message
 */
export const parseApiError = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }

  const apiError = error as AxiosError<any>;

  if (apiError.response?.status === 403) {
    return 'شما دسترسی به این عملیات ندارید';
  }

  if (apiError.response?.status === 404) {
    return 'آیتم درخواستی یافت نشد';
  }

  if (apiError.response?.status === 400) {
    return 'داده‌های ارسالی نامعتبر هستند';
  }

  if (apiError.response?.data?.error) {
    return apiError.response.data.error;
  }

  if (apiError.response?.data?.message) {
    return apiError.response.data.message;
  }

  return 'خطای ناشناخته رخ داد';
};


export const getFields = async (
  token: string,
  filters?: {
    page?: number;
    pageSize?: number;
  }
): Promise<PaginatedResponse<Fields>> => {
  try {
    const params: Record<string, any> = {
      page: filters?.page || 1,
      page_size: filters?.pageSize || 20,
    };

    

    const response = await axios.get<PaginatedResponse<Fields>>(
      `${PRACTICE_API}/fields/teacher/`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        params,
      }
    );

    return response.data;
  } catch (error) { 
    const apiError = error as AxiosError<PaginatedResponse<Fields>>;
    throw new Error(
      apiError.response?.data?.count !== undefined
        ? 'Failed to fetch results'
        : 'Failed to fetch exam results'
    );
  }
};