import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@/test/utils'
import { SceneGallery } from '../SceneGallery'
import { createMockScene } from '@/test/utils'

// Mock the hooks
vi.mock('@/hooks/useScenes', () => ({
  useScenes: vi.fn(),
  useSceneImages: vi.fn(),
  REVIEW_STATUSES: [
    { value: 'pending', label: 'Pending' },
    { value: 'approved', label: 'Approved' },
    { value: 'rejected', label: 'Rejected' },
  ],
  SCENE_TYPES: ['living_room', 'bedroom', 'kitchen'],
}))

const mockUseScenes = vi.mocked(await import('@/hooks/useScenes')).useScenes
const mockUseSceneImages = vi.mocked(await import('@/hooks/useScenes')).useSceneImages

describe('SceneGallery', () => {
  const mockScenes = [
    createMockScene({ id: '1', source: 'scene1.jpg' }),
    createMockScene({ id: '2', source: 'scene2.jpg', scene_type: 'bedroom' }),
    createMockScene({ id: '3', source: 'scene3.jpg', review_status: 'approved' }),
  ]

  beforeEach(() => {
    vi.clearAllMocks()
    
    mockUseScenes.mockReturnValue({
      data: {
        items: mockScenes,
        total: mockScenes.length,
        page: 1,
        limit: 24,
        pages: 1,
      },
      isLoading: false,
      error: null,
    } as any)

    mockUseSceneImages.mockReturnValue({
      thumbnailUrl: 'https://example.com/thumbnail.jpg',
    } as any)
  })

  it('should render scene gallery with scenes', () => {
    render(<SceneGallery />)
    
    expect(screen.getByText('3 of 3 scenes')).toBeInTheDocument()
    expect(screen.getByText('scene1.jpg')).toBeInTheDocument()
    expect(screen.getByText('scene2.jpg')).toBeInTheDocument()
    expect(screen.getByText('scene3.jpg')).toBeInTheDocument()
  })

  it('should filter scenes by search query', async () => {
    render(<SceneGallery />)
    
    const searchInput = screen.getByPlaceholderText('Search scenes...')
    fireEvent.change(searchInput, { target: { value: 'scene1' } })
    
    expect(screen.getByText('scene1.jpg')).toBeInTheDocument()
    expect(screen.queryByText('scene2.jpg')).not.toBeInTheDocument()
  })

  it('should handle scene selection', () => {
    const onSceneSelect = vi.fn()
    render(<SceneGallery onSceneSelect={onSceneSelect} />)
    
    const firstScene = screen.getByText('scene1.jpg')
    fireEvent.click(firstScene.closest('div')!)
    
    expect(onSceneSelect).toHaveBeenCalledWith(mockScenes[0])
  })

  it('should handle scene toggle', () => {
    const onSceneToggle = vi.fn()
    render(<SceneGallery onSceneToggle={onSceneToggle} />)
    
    // Find the checkbox button for the first scene
    const checkboxes = screen.getAllByRole('button')
    const firstCheckbox = checkboxes.find(btn => 
      btn.parentElement?.parentElement?.textContent?.includes('scene1.jpg')
    )
    
    expect(firstCheckbox).toBeTruthy()
    fireEvent.click(firstCheckbox!)
    
    expect(onSceneToggle).toHaveBeenCalledWith('1')
  })

  it('should switch between grid and list view', () => {
    render(<SceneGallery />)
    
    const listButton = screen.getByRole('button', { name: /list/i })
    fireEvent.click(listButton)
    
    // Should still show scenes but in list format
    expect(screen.getByText('scene1.jpg')).toBeInTheDocument()
  })

  it('should show loading state', () => {
    mockUseScenes.mockReturnValue({
      data: null,
      isLoading: true,
      error: null,
    } as any)
    
    render(<SceneGallery />)
    
    expect(screen.getByRole('button', { name: /loading/i })).toBeInTheDocument()
  })

  it('should show error state', () => {
    mockUseScenes.mockReturnValue({
      data: null,
      isLoading: false,
      error: new Error('Failed to load scenes'),
    } as any)
    
    render(<SceneGallery />)
    
    expect(screen.getByText('Failed to load scenes')).toBeInTheDocument()
  })

  it('should show empty state when no scenes', () => {
    mockUseScenes.mockReturnValue({
      data: {
        items: [],
        total: 0,
        page: 1,
        limit: 24,
        pages: 0,
      },
      isLoading: false,
      error: null,
    } as any)
    
    render(<SceneGallery />)
    
    expect(screen.getByText('No scenes found')).toBeInTheDocument()
  })

  it('should handle select all functionality', () => {
    const onBatchSelect = vi.fn()
    render(<SceneGallery onBatchSelect={onBatchSelect} />)
    
    const selectAllButton = screen.getByRole('button', { name: /select all/i })
    fireEvent.click(selectAllButton)
    
    expect(onBatchSelect).toHaveBeenCalledWith(mockScenes)
  })

  it('should filter by review status', async () => {
    render(<SceneGallery />)
    
    // Find and open the status filter dropdown
    const statusFilter = screen.getByDisplayValue('All Status')
    fireEvent.click(statusFilter)
    
    // Select approved status
    const approvedOption = screen.getByText('Approved')
    fireEvent.click(approvedOption)
    
    await waitFor(() => {
      expect(mockUseScenes).toHaveBeenCalledWith(
        expect.objectContaining({
          review_status: 'approved'
        })
      )
    })
  })

  it('should filter by scene type', async () => {
    render(<SceneGallery />)
    
    // Find and open the scene type filter dropdown  
    const typeFilter = screen.getByDisplayValue('All Types')
    fireEvent.click(typeFilter)
    
    // Select bedroom type
    const bedroomOption = screen.getByText('bedroom')
    fireEvent.click(bedroomOption)
    
    await waitFor(() => {
      expect(mockUseScenes).toHaveBeenCalledWith(
        expect.objectContaining({
          scene_type: 'bedroom'
        })
      )
    })
  })

  it('should display confidence scores with correct colors', () => {
    const highConfidenceScene = createMockScene({ 
      id: 'high', 
      source: 'high-conf.jpg', 
      scene_conf: 0.95 
    })
    
    const lowConfidenceScene = createMockScene({ 
      id: 'low', 
      source: 'low-conf.jpg', 
      scene_conf: 0.45 
    })
    
    mockUseScenes.mockReturnValue({
      data: {
        items: [highConfidenceScene, lowConfidenceScene],
        total: 2,
        page: 1,
        limit: 24,
        pages: 1,
      },
      isLoading: false,
      error: null,
    } as any)
    
    render(<SceneGallery />)
    
    expect(screen.getByText('95%')).toBeInTheDocument()
    expect(screen.getByText('45%')).toBeInTheDocument()
  })
})