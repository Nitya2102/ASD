import { CombinedResult, RiskLevel } from '@/types/asd';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { AlertTriangle, CheckCircle, Info } from 'lucide-react';

interface ResultsDisplayProps {
  result: CombinedResult;
  imagePreview: string | null;
  onReset: () => void;
}

function RiskBadge({ level }: { level: RiskLevel }) {
  const config = {
    LOW: { className: 'risk-badge-low', icon: CheckCircle, label: 'Low Risk' },
    MODERATE: { className: 'risk-badge-moderate', icon: Info, label: 'Moderate Risk' },
    HIGH: { className: 'risk-badge-high', icon: AlertTriangle, label: 'High Risk' },
  };

  const { className, icon: Icon, label } = config[level];

  return (
    <span className={cn('risk-badge gap-1.5', className)}>
      <Icon className="w-4 h-4" />
      {label}
    </span>
  );
}

function ConfidenceBar({ value, label }: { value: number; label: string }) {
  const percentage = Math.round(value * 100);
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-sm">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{percentage}%</span>
      </div>
      <div className="h-2 bg-secondary rounded-full overflow-hidden">
        <div
          className="h-full bg-primary transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

export function ResultsDisplay({ result, imagePreview, onReset }: ResultsDisplayProps) {
  const hasImageAnalysis = result.imageDetails !== null;

  return (
    <div className="space-y-8 animate-slide-up">
      {/* Header */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Screening Results</h2>
        <div className="flex items-center gap-4">
          <RiskBadge level={result.riskLevel} />
          <span className="text-muted-foreground text-sm">
            Combined confidence: {Math.round(result.confidence * 100)}%
          </span>
        </div>
      </div>

      {/* Main results grid */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Questionnaire Results */}
        <div className="clinical-card space-y-4">
          <h3 className="font-semibold text-lg">Questionnaire Analysis</h3>
          
          <div className="space-y-4">
            <ConfidenceBar
              value={result.questionnaireDetails.confidence}
              label="ML Model Confidence"
            />
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Total Score</span>
                <p className="font-medium text-lg">{result.questionnaireDetails.totalScore}/10</p>
              </div>
              <div>
                <span className="text-muted-foreground">Contribution</span>
                <p className="font-medium text-lg">{Math.round(result.mlContribution * 100)}%</p>
              </div>
            </div>

            {result.questionnaireDetails.concerns.length > 0 && (
              <div className="space-y-2">
                <p className="text-sm font-medium">Areas of Concern</p>
                <ul className="text-sm text-muted-foreground space-y-1">
                  {result.questionnaireDetails.concerns.map((concern, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-warning mt-0.5">•</span>
                      {concern}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>

        {/* Image Analysis Results */}
        <div className="clinical-card space-y-4">
          <h3 className="font-semibold text-lg">Image Analysis</h3>
          
          {hasImageAnalysis ? (
            <div className="space-y-4">
              <ConfidenceBar
                value={result.imageDetails.confidence}
                label="CNN Model Confidence"
              />

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Prediction</span>
                  <p className="font-medium text-lg">
                    {result.imageDetails.prediction === 1 ? 'Elevated Risk' : 'Low Risk'}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Contribution</span>
                  <p className="font-medium text-lg">{Math.round(result.cnnContribution * 100)}%</p>
                </div>
              </div>

              {/* Attention regions */}
              <div className="space-y-2">
                <p className="text-sm font-medium">Attention Regions</p>
                <div className="flex flex-wrap gap-2">
                  {result.imageDetails.attentionRegions.map((region, i) => (
                    <span
                      key={i}
                      className="px-2 py-1 bg-accent rounded text-xs font-medium"
                    >
                      {region.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <p>Image analysis was skipped</p>
              <p className="text-sm mt-1">Results based on questionnaire only</p>
            </div>
          )}
        </div>
      </div>

      {/* XAI Visualizations */}
      {hasImageAnalysis && imagePreview && (
        <div className="clinical-card space-y-4">
          <h3 className="font-semibold text-lg">Explainable AI Visualizations</h3>
          
          <div className="grid md:grid-cols-2 gap-6">
            {/* Original Image with Grad-CAM */}
            <div className="space-y-2">
              <p className="text-sm font-medium">Grad-CAM Heatmap</p>
              <div className="heatmap-container">
                <img
                  src={imagePreview}
                  alt="Original"
                  className="w-full rounded-lg"
                />
                {result.imageDetails.heatmapBase64 && (
                  <img
                    src={`data:image/png;base64,${result.imageDetails.heatmapBase64}`}
                    alt="Grad-CAM heatmap"
                    className="heatmap-overlay opacity-60"
                  />
                )}
                {/* Simulated heatmap overlay for demo */}
                <div className="absolute inset-0 bg-gradient-to-br from-transparent via-yellow-500/20 to-red-500/30 rounded-lg pointer-events-none" />
              </div>
              <p className="text-xs text-muted-foreground">
                Warmer colors indicate regions of higher model attention
              </p>
            </div>

            {/* LIME Explanation */}
            <div className="space-y-2">
              <p className="text-sm font-medium">LIME Explanation</p>
              <div className="heatmap-container">
                <img
                  src={imagePreview}
                  alt="LIME"
                  className="w-full rounded-lg"
                />
                {/* Simulated LIME overlay for demo */}
                <div className="absolute inset-0 pointer-events-none">
                  <div className="absolute top-[20%] left-[30%] w-[40%] h-[15%] border-2 border-primary/50 rounded bg-primary/10" />
                  <div className="absolute top-[40%] left-[35%] w-[30%] h-[10%] border-2 border-primary/30 rounded bg-primary/5" />
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                Highlighted regions show features most influential to the prediction
              </p>
            </div>
          </div>

          {/* Facial Region Scores */}
          <div className="space-y-3">
            <p className="text-sm font-medium">Regional Attention Scores</p>
            <div className="grid sm:grid-cols-2 gap-3">
              {result.imageDetails.facialRegions.map((region, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg">
                  <div>
                    <p className="font-medium text-sm">{region.region}</p>
                    <p className="text-xs text-muted-foreground">{region.clinical_relevance}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-lg font-semibold text-primary">
                      {Math.round(region.attention_score * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* LLM Explanation */}
      {hasImageAnalysis && result.imageDetails.llmExplanation && (
        <div className="clinical-card space-y-4">
          <h3 className="font-semibold text-lg">Clinical Interpretation</h3>
          <div className="prose prose-sm max-w-none text-foreground">
            {result.imageDetails.llmExplanation.split('\n\n').map((paragraph, i) => {
              if (paragraph.startsWith('**') && paragraph.includes(':**')) {
                const [title, ...content] = paragraph.split(':**');
                return (
                  <div key={i} className="mb-4">
                    <h4 className="font-semibold text-sm mb-1">
                      {title.replace(/\*\*/g, '')}
                    </h4>
                    <p className="text-muted-foreground">{content.join(':**')}</p>
                  </div>
                );
              }
              return (
                <p key={i} className="text-muted-foreground mb-3">
                  {paragraph}
                </p>
              );
            })}
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div className="clinical-card space-y-4">
        <h3 className="font-semibold text-lg">Recommendations</h3>
        <ul className="space-y-2">
          {result.questionnaireDetails.recommendations.map((rec, i) => (
            <li key={i} className="flex items-start gap-3 text-sm">
              <span className="flex-shrink-0 w-5 h-5 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-medium">
                {i + 1}
              </span>
              <span className="text-muted-foreground">{rec}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Disclaimer */}
      <div className="bg-accent/50 rounded-lg p-4 text-sm text-muted-foreground">
        <p className="font-medium text-foreground mb-1">Important Disclaimer</p>
        <p>
          This screening tool is intended for preliminary assessment only and does not provide 
          a clinical diagnosis. Results should be interpreted by qualified healthcare professionals. 
          If you have concerns about your child's development, please consult with a developmental 
          pediatrician or other qualified specialist.
        </p>
      </div>

      {/* Actions */}
      <div className="flex justify-between pt-4">
        <Button variant="outline" onClick={() => window.print()}>
          Print Results
        </Button>
        <Button onClick={onReset}>
          Start New Screening
        </Button>
      </div>
    </div>
  );
}
