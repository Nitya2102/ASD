// ASD Screening Types

export interface PatientInfo {
  age: number;
  sex: 'male' | 'female';
  jaundice: 'yes' | 'no';
  familyAsd: 'yes' | 'no';
}

export interface QuestionnaireResponses {
  A1: 'yes' | 'no' | null;
  A2: 'yes' | 'no' | null;
  A3: 'yes' | 'no' | null;
  A4: 'yes' | 'no' | null;
  A5: 'yes' | 'no' | null;
  A6: 'yes' | 'no' | null;
  A7: 'yes' | 'no' | null;
  A8: 'yes' | 'no' | null;
  A9: 'yes' | 'no' | null;
  A10: 'yes' | 'no' | null;
}

export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH';

export interface QuestionnaireResult {
  source: 'questionnaire';
  prediction: number;
  confidence: number;
  riskLevel: RiskLevel;
  totalScore: number;
  concerns: string[];
  recommendations: string[];
}

export interface FacialRegion {
  region: string;
  attention_score: number;
  clinical_relevance: string;
}

export interface ImageResult {
  source: 'image';
  prediction: number;
  confidence: number;
  heatmapBase64: string;
  limeBase64?: string;
  attentionRegions: string[];
  llmExplanation: string;
  facialRegions: FacialRegion[] | Record<string, any>;
}

export interface CombinedResult {
  prediction: number;
  predictionLabel: 'ELEVATED_RISK' | 'LOW_RISK';
  confidence: number;
  riskLevel: RiskLevel;
  mlContribution: number;
  cnnContribution: number;
  questionnaireDetails: QuestionnaireResult;
  imageDetails: ImageResult | null;
}

export interface ScreeningState {
  step: 'patient-info' | 'questionnaire' | 'image-analysis' | 'results';
  patientInfo: PatientInfo | null;
  responses: QuestionnaireResponses;
  imageFile: File | null;
  imagePreview: string | null;
  questionnaireResult: QuestionnaireResult | null;
  imageResult: ImageResult | null;
  combinedResult: CombinedResult | null;
  isLoading: boolean;
  error: string | null;
}

export const QUESTIONNAIRE_QUESTIONS = [
  { id: 'A1', text: 'Does your child look at you when you call his/her name?' },
  { id: 'A2', text: 'How easy is it for you to get eye contact with your child?' },
  { id: 'A3', text: 'Does your child point to indicate that s/he wants something?' },
  { id: 'A4', text: 'Does your child point to share interest with you?' },
  { id: 'A5', text: 'Does your child pretend (e.g., care for dolls, talk on toy phone)?' },
  { id: 'A6', text: 'Does your child follow where you\'re looking?' },
  { id: 'A7', text: 'If someone in the family is visibly upset, does your child show signs of wanting to comfort them?' },
  { id: 'A8', text: 'Would you describe your child\'s first words as typical?' },
  { id: 'A9', text: 'Does your child use simple gestures (e.g., wave goodbye)?' },
  { id: 'A10', text: 'Does your child stare at nothing with no apparent purpose?' },
] as const;
