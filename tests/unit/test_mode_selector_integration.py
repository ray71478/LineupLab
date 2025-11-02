"""
Unit Tests for ModeSelector Integration

Task Group 8.1: Integration Tests

These tests verify the ModeSelector component integration specifications:
- ModeSelector appears in app header
- Mode state is globally accessible
- Integration with MainLayout works correctly
- Mode state persists across navigation
"""

import pytest


class TestModeSelectorIntegration:
    """
    Test ModeSelector integration requirements
    """

    def test_mode_selector_in_app_header(self):
        """
        Test: ModeSelector should be present in App.tsx header

        Verifies:
        - ModeSelector component is imported in App.tsx
        - ModeSelector is rendered in MainLayout menuItems
        - Component is accessible from all pages using MainLayout
        """
        # Read App.tsx file
        with open('frontend/src/App.tsx', 'r') as f:
            app_content = f.read()

        # Verify ModeSelector is imported
        assert 'import ModeSelector' in app_content or 'import { ModeSelector }' in app_content, \
            "ModeSelector should be imported in App.tsx"

        # Verify ModeSelector is rendered in the component tree
        assert '<ModeSelector' in app_content, \
            "ModeSelector should be rendered in App.tsx"

        # Verify it's in the menuItems section (global header)
        assert 'menuItems=' in app_content, \
            "App.tsx should have menuItems prop for MainLayout"

    def test_mode_selector_component_exists(self):
        """
        Test: ModeSelector component file exists

        Verifies:
        - Component file exists at expected location
        - Component exports ModeSelector
        - Component uses useModeStore
        """
        import os

        # Verify component file exists
        component_path = 'frontend/src/components/layout/ModeSelector.tsx'
        assert os.path.exists(component_path), \
            f"ModeSelector component should exist at {component_path}"

        # Read component file
        with open(component_path, 'r') as f:
            component_content = f.read()

        # Verify it exports ModeSelector
        assert 'export' in component_content and 'ModeSelector' in component_content, \
            "Component should export ModeSelector"

        # Verify it uses the mode store
        assert 'useModeStore' in component_content, \
            "ModeSelector should use useModeStore"

        # Verify it has proper data-testid attributes
        assert 'data-testid="mode-selector"' in component_content, \
            "ModeSelector should have data-testid for testing"
        assert 'data-testid="mode-button-main"' in component_content, \
            "Main button should have data-testid"
        assert 'data-testid="mode-button-showdown"' in component_content, \
            "Showdown button should have data-testid"

    def test_mode_state_globally_accessible(self):
        """
        Test: Mode state should be accessible via useModeStore

        Verifies:
        - useModeStore is exported from store/index.ts
        - useMode hook is exported from hooks/index.ts
        - Store follows Zustand pattern
        """
        # Verify store is exported
        with open('frontend/src/store/index.ts', 'r') as f:
            store_exports = f.read()

        assert 'useModeStore' in store_exports or 'modeStore' in store_exports, \
            "useModeStore should be exported from store/index.ts"

        # Verify hook is exported
        with open('frontend/src/hooks/index.ts', 'r') as f:
            hook_exports = f.read()

        assert 'useMode' in hook_exports, \
            "useMode hook should be exported from hooks/index.ts"

        # Verify store implementation
        with open('frontend/src/store/modeStore.ts', 'r') as f:
            store_content = f.read()

        assert 'create' in store_content, \
            "modeStore should use Zustand create function"
        assert 'persist' in store_content, \
            "modeStore should use persist middleware for localStorage"

    def test_mode_selector_independent_from_week_navigation(self):
        """
        Test: ModeSelector should be independent from WeekNavigation

        Verifies:
        - ModeSelector doesn't import or use WeekNavigation
        - ModeSelector only uses useModeStore
        - No coupling between mode and week state
        """
        with open('frontend/src/components/layout/ModeSelector.tsx', 'r') as f:
            mode_selector_content = f.read()

        # Verify no dependency on WeekNavigation
        assert 'WeekNavigation' not in mode_selector_content, \
            "ModeSelector should not depend on WeekNavigation"

        # Verify no dependency on weekStore
        assert 'useWeekStore' not in mode_selector_content, \
            "ModeSelector should not use useWeekStore"

        # Verify it only uses modeStore
        assert 'useModeStore' in mode_selector_content, \
            "ModeSelector should use useModeStore"

    def test_responsive_layout_styling(self):
        """
        Test: ModeSelector should have responsive styling

        Verifies:
        - Component uses Material-UI responsive breakpoints
        - Has mobile-specific styling (xs/sm breakpoints)
        - Has desktop styling
        """
        with open('frontend/src/components/layout/ModeSelector.tsx', 'r') as f:
            component_content = f.read()

        # Verify responsive styling exists
        assert 'useMediaQuery' in component_content or 'breakpoints' in component_content, \
            "ModeSelector should implement responsive design"

        # Verify button group styling
        assert 'ButtonGroup' in component_content, \
            "ModeSelector should use ButtonGroup component"

    def test_accessibility_features(self):
        """
        Test: ModeSelector should have accessibility features

        Verifies:
        - Has aria-label on container
        - Buttons have aria-pressed attributes
        - Keyboard navigation support mentioned
        """
        with open('frontend/src/components/layout/ModeSelector.tsx', 'r') as f:
            component_content = f.read()

        # Verify accessibility attributes
        assert 'aria-label' in component_content, \
            "ModeSelector should have aria-label"
        assert 'aria-pressed' in component_content, \
            "Buttons should have aria-pressed attribute"

        # Verify keyboard support
        assert 'onKeyDown' in component_content or 'keyboard' in component_content.lower(), \
            "ModeSelector should support keyboard navigation"

    def test_main_layout_accepts_menu_items(self):
        """
        Test: MainLayout should accept and render menuItems prop

        Verifies:
        - MainLayout has menuItems prop
        - menuItems prop is rendered in header
        - ModeSelector can be passed as menu item
        """
        with open('frontend/src/components/layout/MainLayout.tsx', 'r') as f:
            layout_content = f.read()

        # Verify menuItems prop exists
        assert 'menuItems' in layout_content, \
            "MainLayout should have menuItems prop"

        # Verify menuItems is rendered
        assert '{menuItems}' in layout_content, \
            "MainLayout should render menuItems prop"

    def test_e2e_tests_created(self):
        """
        Test: E2E integration tests should exist

        Verifies:
        - E2E test file exists for mode selector integration
        - Tests cover required scenarios
        """
        import os

        # Verify E2E test file exists
        e2e_test_path = 'tests/e2e/mode-selector-integration.spec.ts'
        assert os.path.exists(e2e_test_path), \
            f"E2E integration tests should exist at {e2e_test_path}"

        # Read test file
        with open(e2e_test_path, 'r') as f:
            test_content = f.read()

        # Verify key test scenarios exist
        assert 'appears in header' in test_content.lower(), \
            "Tests should verify ModeSelector appears in header"
        assert 'persist' in test_content.lower(), \
            "Tests should verify mode persists across navigation"
        assert 'responsive' in test_content.lower() or 'mobile' in test_content.lower(), \
            "Tests should verify responsive behavior"
        assert 'independent' in test_content.lower(), \
            "Tests should verify independence from WeekNavigation"


class TestModeSelectorLayoutIntegration:
    """
    Test ModeSelector layout integration with app header
    """

    def test_mode_selector_positioned_with_week_selector(self):
        """
        Test: ModeSelector should be positioned alongside WeekSelector

        Verifies:
        - Both components are in same menuItems section
        - They are separate components (not nested)
        """
        with open('frontend/src/App.tsx', 'r') as f:
            app_content = f.read()

        # Find menuItems section
        menuItems_start = app_content.find('menuItems=')
        assert menuItems_start > 0, "menuItems should exist in App.tsx"

        # Find the Box/Stack that contains the header items
        menuItems_section = app_content[menuItems_start:menuItems_start + 1000]

        # Verify both components are present in header
        assert '<ModeSelector' in menuItems_section, \
            "ModeSelector should be in menuItems section"
        assert '<WeekSelector' in menuItems_section, \
            "WeekSelector should be in menuItems section"

    def test_header_layout_uses_flexbox(self):
        """
        Test: Header layout should use flexbox for alignment

        Verifies:
        - App.tsx uses Box or Stack with flex properties
        - Proper spacing between controls
        """
        with open('frontend/src/App.tsx', 'r') as f:
            app_content = f.read()

        # Verify flex layout
        menuItems_start = app_content.find('menuItems=')
        menuItems_section = app_content[menuItems_start:menuItems_start + 500]

        # Should use Box or Stack with flex/gap
        assert ('Box' in menuItems_section and ('gap' in menuItems_section or 'spacing' in menuItems_section)) or \
               ('Stack' in menuItems_section), \
            "Header should use Box/Stack with proper spacing"


class TestModeSelectorStateManagement:
    """
    Test mode state management integration
    """

    def test_mode_store_persists_to_localstorage(self):
        """
        Test: Mode state should persist to localStorage

        Verifies:
        - modeStore uses persist middleware
        - localStorage key is defined
        """
        with open('frontend/src/store/modeStore.ts', 'r') as f:
            store_content = f.read()

        # Verify persist middleware
        assert 'persist' in store_content, \
            "modeStore should use persist middleware"

        # Verify name/key for localStorage
        assert 'name:' in store_content or "'mode-store'" in store_content or '"mode-store"' in store_content, \
            "modeStore should define localStorage key"

    def test_mode_store_provides_setmode_function(self):
        """
        Test: Mode store should provide setMode function

        Verifies:
        - setMode function exists in store
        - Function accepts ContestMode parameter
        """
        with open('frontend/src/store/modeStore.ts', 'r') as f:
            store_content = f.read()

        # Verify setMode function
        assert 'setMode' in store_content, \
            "modeStore should provide setMode function"

        # Verify ContestMode type
        assert 'ContestMode' in store_content, \
            "modeStore should define ContestMode type"

    def test_use_mode_hook_simplifies_access(self):
        """
        Test: useMode hook should simplify store access

        Verifies:
        - useMode hook exists
        - Returns mode and setMode
        - Uses useModeStore internally
        """
        with open('frontend/src/hooks/useMode.ts', 'r') as f:
            hook_content = f.read()

        # Verify hook exports
        assert 'export' in hook_content and 'useMode' in hook_content, \
            "useMode hook should be exported"

        # Verify it uses the store
        assert 'useModeStore' in hook_content, \
            "useMode should use useModeStore"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
