import { useState } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts'
import { Activity, Target, TrendingUp, Eye } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useModelPerformance } from '@/hooks/useStats'
import type { StatsQuery } from '@/types/stats'

interface ModelPerformanceChartProps {
  query?: StatsQuery
  className?: string
}

type ChartType = 'confidence' | 'accuracy' | 'radar'

const MODEL_TYPE_LABELS = {
  scene_classifier: 'Scene Classifier',
  style_classifier: 'Style Classifier', 
  object_detector: 'Object Detector',
  material_detector: 'Material Detector'
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444']

export function ModelPerformanceChart({ query, className }: ModelPerformanceChartProps) {
  const [chartType, setChartType] = useState<ChartType>('confidence')
  const [selectedModel, setSelectedModel] = useState<string>('all')
  
  const { data: modelPerformance, isLoading, error } = useModelPerformance(query)

  const getFilteredModels = () => {
    if (!modelPerformance) return []
    
    if (selectedModel === 'all') {
      return modelPerformance
    }
    
    return modelPerformance.filter(model => model.model_type === selectedModel)
  }

  const getConfidenceData = () => {
    const models = getFilteredModels()
    
    return models.map(model => ({
      name: MODEL_TYPE_LABELS[model.model_type],
      avgConfidence: (model.average_confidence * 100),
      totalPredictions: model.total_predictions,
      modelType: model.model_type,
      ...model.confidence_distribution.reduce((acc, bucket, index) => {
        acc[`bucket${index}`] = bucket.percentage
        return acc
      }, {} as Record<string, number>)
    }))
  }

  const getAccuracyData = () => {
    const models = getFilteredModels()
    
    return models.flatMap(model => 
      model.accuracy_by_class?.map(classAcc => ({
        model: MODEL_TYPE_LABELS[model.model_type],
        className: classAcc.class_name,
        precision: classAcc.precision * 100,
        recall: classAcc.recall * 100,
        f1Score: classAcc.f1_score * 100,
        support: classAcc.support
      })) || []
    )
  }

  const getRadarData = () => {
    const models = getFilteredModels()
    
    return models.map(model => ({
      model: MODEL_TYPE_LABELS[model.model_type],
      confidence: model.average_confidence * 100,
      predictions: Math.min((model.total_predictions / 10000) * 100, 100), // Normalize to 0-100
      accuracy: model.accuracy_by_class 
        ? (model.accuracy_by_class.reduce((sum, acc) => sum + acc.f1_score, 0) / model.accuracy_by_class.length) * 100
        : 0,
    }))
  }

  const getModelSummary = () => {
    const models = getFilteredModels()
    
    if (models.length === 0) return null
    
    const totalPredictions = models.reduce((sum, model) => sum + model.total_predictions, 0)
    const avgConfidence = models.reduce((sum, model) => sum + model.average_confidence, 0) / models.length
    
    return {
      totalModels: models.length,
      totalPredictions,
      avgConfidence: avgConfidence * 100,
      lastUpdated: models[0]?.last_updated
    }
  }

  const confidenceData = getConfidenceData()
  const accuracyData = getAccuracyData()
  const radarData = getRadarData()
  const summary = getModelSummary()

  if (error) {
    return (
      <div className={`bg-card border rounded-lg p-6 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <Activity className="h-5 w-5 text-destructive" />
          <h3 className="text-lg font-semibold">Model Performance</h3>
          <Badge variant="destructive">Error</Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Unable to load model performance data
        </p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className={`bg-card border rounded-lg p-6 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <Activity className="h-5 w-5 animate-pulse" />
          <h3 className="text-lg font-semibold">Model Performance</h3>
        </div>
        <div className="h-80 bg-muted animate-pulse rounded" />
      </div>
    )
  }

  return (
    <div className={`bg-card border rounded-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Activity className="h-5 w-5" />
          <h3 className="text-lg font-semibold">Model Performance</h3>
        </div>
        
        <div className="flex items-center space-x-2">
          <Select value={selectedModel} onValueChange={setSelectedModel}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Models</SelectItem>
              <SelectItem value="scene_classifier">Scene Classifier</SelectItem>
              <SelectItem value="style_classifier">Style Classifier</SelectItem>
              <SelectItem value="object_detector">Object Detector</SelectItem>
              <SelectItem value="material_detector">Material Detector</SelectItem>
            </SelectContent>
          </Select>
          
          <div className="flex space-x-1">
            <Button
              variant={chartType === 'confidence' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setChartType('confidence')}
            >
              <TrendingUp className="h-4 w-4" />
            </Button>
            <Button
              variant={chartType === 'accuracy' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setChartType('accuracy')}
            >
              <Target className="h-4 w-4" />
            </Button>
            <Button
              variant={chartType === 'radar' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setChartType('radar')}
            >
              <Eye className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center p-3 bg-muted/50 rounded-md">
            <div className="text-2xl font-bold text-blue-600">
              {summary.totalModels}
            </div>
            <div className="text-xs text-muted-foreground">Active Models</div>
          </div>
          
          <div className="text-center p-3 bg-muted/50 rounded-md">
            <div className="text-2xl font-bold text-green-600">
              {summary.totalPredictions.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground">Total Predictions</div>
          </div>
          
          <div className="text-center p-3 bg-muted/50 rounded-md">
            <div className="text-2xl font-bold text-purple-600">
              {summary.avgConfidence.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground">Avg Confidence</div>
          </div>
        </div>
      )}

      {/* Chart Area */}
      <div className="h-80">
        {(!modelPerformance || modelPerformance.length === 0) ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            No model performance data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            {(() => {
              if (chartType === 'confidence') {
                return (
                  <BarChart data={confidenceData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                    <XAxis 
                      dataKey="name" 
                      tick={{ fontSize: 12 }}
                      stroke="#6b7280"
                      angle={-45}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis 
                      tick={{ fontSize: 12 }} 
                      stroke="#6b7280"
                      domain={[0, 100]}
                      label={{ value: 'Confidence (%)', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                      }}
                      labelStyle={{ color: '#f9fafb' }}
                      formatter={(value: number) => [`${value.toFixed(1)}%`, 'Avg Confidence']}
                    />
                    <Bar 
                      dataKey="avgConfidence" 
                      fill="#3b82f6"
                      name="Average Confidence"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                )
              }
              
              if (chartType === 'accuracy' && accuracyData.length > 0) {
                return (
                  <BarChart data={accuracyData.slice(0, 10)}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                    <XAxis 
                      dataKey="className" 
                      tick={{ fontSize: 12 }}
                      stroke="#6b7280"
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis 
                      tick={{ fontSize: 12 }} 
                      stroke="#6b7280"
                      domain={[0, 100]}
                      label={{ value: 'Score (%)', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                      }}
                      formatter={(value: number) => [`${value.toFixed(1)}%`]}
                    />
                    <Legend />
                    
                    <Bar dataKey="precision" fill="#10b981" name="Precision" />
                    <Bar dataKey="recall" fill="#f59e0b" name="Recall" />
                    <Bar dataKey="f1Score" fill="#8b5cf6" name="F1 Score" />
                  </BarChart>
                )
              }
              
              if (chartType === 'radar') {
                return (
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#374151" />
                    <PolarAngleAxis 
                      tick={{ fontSize: 12, fill: '#6b7280' }}
                      tickFormatter={(value) => {
                        const labels = { confidence: 'Confidence', predictions: 'Volume', accuracy: 'Accuracy' }
                        return labels[value as keyof typeof labels] || value
                      }}
                    />
                    <PolarRadiusAxis 
                      tick={{ fontSize: 10, fill: '#6b7280' }}
                      domain={[0, 100]}
                      tickCount={5}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1f2937',
                        border: '1px solid #374151',
                        borderRadius: '8px',
                      }}
                    />
                    
                    {radarData.map((entry, index) => (
                      <Radar
                        key={entry.model}
                        name={entry.model}
                        dataKey={entry.model}
                        stroke={COLORS[index % COLORS.length]}
                        fill={COLORS[index % COLORS.length]}
                        fillOpacity={0.1}
                        strokeWidth={2}
                      />
                    ))}
                    <Legend />
                  </RadarChart>
                )
              }
              
              return null
            })()}
          </ResponsiveContainer>
        )}
      </div>

      {/* Model Details */}
      {selectedModel !== 'all' && modelPerformance && (
        <div className="mt-4 pt-4 border-t">
          {modelPerformance
            .filter(model => model.model_type === selectedModel)
            .map(model => (
              <div key={model.model_name} className="text-sm">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{model.model_name}</span>
                  <Badge variant="outline">
                    {model.total_predictions.toLocaleString()} predictions
                  </Badge>
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  Last updated: {new Date(model.last_updated).toLocaleString()}
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  )
}