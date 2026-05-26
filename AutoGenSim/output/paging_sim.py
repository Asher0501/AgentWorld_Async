#!/usr/bin/env python3
"""
Memory Paging Simulator
Implements Page, Frame, PageTable classes and FIFO/LRU/OPT replacement algorithms
"""

from collections import deque

class Page:
    """Represents a page in the process's virtual address space"""
    def __init__(self, page_id):
        self.page_id = page_id
        self.loaded = False  # Whether it's in a frame
        self.frame_id = None  # Which frame it's loaded into
        
    def __repr__(self):
        return f"Page({self.page_id})"


class Frame:
    """Represents a physical frame in memory"""
    def __init__(self, frame_id):
        self.frame_id = frame_id
        self.page = None  # Page currently in this frame
        self.occupied = False
        
    def __repr__(self):
        if self.occupied:
            return f"Frame({self.frame_id}: Page{self.page.page_id})"
        return f"Frame({self.frame_id}: empty)"


class PageTable:
    """Manages the mapping from pages to frames"""
    def __init__(self, num_frames):
        self.num_frames = num_frames
        self.frames = [Frame(i) for i in range(num_frames)]
        self.page_map = {}  # page_id -> Page object
        self.page_faults = 0
        self.access_count = 0
        
    def get_page(self, page_id):
        """Get or create a page entry"""
        if page_id not in self.page_map:
            self.page_map[page_id] = Page(page_id)
        return self.page_map[page_id]
    
    def is_page_loaded(self, page_id):
        """Check if a page is already in memory"""
        if page_id in self.page_map:
            return self.page_map[page_id].loaded
        return False
    
    def reset(self):
        """Reset the page table for a new algorithm run"""
        for frame in self.frames:
            frame.page = None
            frame.occupied = False
        for page in self.page_map.values():
            page.loaded = False
            page.frame_id = None
        self.page_faults = 0
        self.access_count = 0


class PagingSimulator:
    """Main simulator class with FIFO, LRU, OPT algorithms"""
    
    def __init__(self, num_frames, page_sequence):
        self.num_frames = num_frames
        self.page_sequence = page_sequence
        self.total_accesses = len(page_sequence)
        
    def fifo(self):
        """First-In-First-Out page replacement algorithm"""
        page_table = PageTable(self.num_frames)
        queue = deque()  # Queue of page_ids in FIFO order
        faults = 0
        
        for page_id in self.page_sequence:
            page_table.access_count += 1
            
            if page_table.is_page_loaded(page_id):
                # Page hit - do nothing for FIFO
                continue
            
            # Page fault
            faults += 1
            page = page_table.get_page(page_id)
            
            if len(queue) < self.num_frames:
                # There's a free frame
                frame_id = len(queue)
            else:
                # Need to evict the oldest page
                oldest_page_id = queue.popleft()
                oldest_page = page_table.get_page(oldest_page_id)
                frame_id = oldest_page.frame_id
                # Remove old page from frame
                oldest_page.loaded = False
                oldest_page.frame_id = None
                page_table.frames[frame_id].occupied = False
                page_table.frames[frame_id].page = None
            
            # Load page into frame
            page_table.frames[frame_id].page = page
            page_table.frames[frame_id].occupied = True
            page.loaded = True
            page.frame_id = frame_id
            queue.append(page_id)
        
        return faults, self._page_fault_rate(faults)
    
    def lru(self):
        """Least Recently Used page replacement algorithm"""
        page_table = PageTable(self.num_frames)
        # Track last used time for each page_id
        last_used = {}
        faults = 0
        current_time = 0
        
        for page_id in self.page_sequence:
            current_time += 1
            page_table.access_count += 1
            
            if page_table.is_page_loaded(page_id):
                # Page hit - update last used time
                last_used[page_id] = current_time
                continue
            
            # Page fault
            faults += 1
            page = page_table.get_page(page_id)
            
            # Check if there's a free frame
            free_frame = None
            for frame in page_table.frames:
                if not frame.occupied:
                    free_frame = frame.frame_id
                    break
            
            if free_frame is not None:
                frame_id = free_frame
            else:
                # Evict the least recently used page
                # Find the page in memory with smallest last_used time
                lru_page_id = None
                min_time = float('inf')
                for frame in page_table.frames:
                    if frame.occupied and frame.page is not None:
                        pid = frame.page.page_id
                        if last_used.get(pid, 0) < min_time:
                            min_time = last_used.get(pid, 0)
                            lru_page_id = pid
                
                # Evict that page
                evict_page = page_table.get_page(lru_page_id)
                frame_id = evict_page.frame_id
                evict_page.loaded = False
                evict_page.frame_id = None
                page_table.frames[frame_id].occupied = False
                page_table.frames[frame_id].page = None
            
            # Load page into frame
            page_table.frames[frame_id].page = page
            page_table.frames[frame_id].occupied = True
            page.loaded = True
            page.frame_id = frame_id
            last_used[page_id] = current_time
        
        return faults, self._page_fault_rate(faults)
    
    def opt(self):
        """Optimal (MIN) page replacement algorithm - replaces page that will be used furthest in future"""
        page_table = PageTable(self.num_frames)
        faults = 0
        
        for i, page_id in enumerate(self.page_sequence):
            page_table.access_count += 1
            
            if page_table.is_page_loaded(page_id):
                continue
            
            # Page fault
            faults += 1
            page = page_table.get_page(page_id)
            
            # Check if there's a free frame
            free_frame = None
            for frame in page_table.frames:
                if not frame.occupied:
                    free_frame = frame.frame_id
                    break
            
            if free_frame is not None:
                frame_id = free_frame
            else:
                # Need to evict: find the page that will be used furthest in future (or never)
                farthest_dist = -1
                evict_page_id = None
                
                for frame in page_table.frames:
                    if frame.occupied and frame.page is not None:
                        pid = frame.page.page_id
                        # Find next occurrence of this page after current position
                        next_use = self.total_accesses  # Default: never used again
                        for j in range(i + 1, self.total_accesses):
                            if self.page_sequence[j] == pid:
                                next_use = j
                                break
                        
                        # Find the page with farthest next use
                        if next_use > farthest_dist:
                            farthest_dist = next_use
                            evict_page_id = pid
                
                # Evict the selected page
                evict_page = page_table.get_page(evict_page_id)
                frame_id = evict_page.frame_id
                evict_page.loaded = False
                evict_page.frame_id = None
                page_table.frames[frame_id].occupied = False
                page_table.frames[frame_id].page = None
            
            # Load page into frame
            page_table.frames[frame_id].page = page
            page_table.frames[frame_id].occupied = True
            page.loaded = True
            page.frame_id = frame_id
        
        return faults, self._page_fault_rate(faults)
    
    def _page_fault_rate(self, faults):
        """Calculate page fault rate"""
        return faults / self.total_accesses if self.total_accesses > 0 else 0
    
    def run_all(self):
        """Run all three algorithms and print results"""
        print("=" * 60)
        print(f"PAGING SIMULATOR RESULTS")
        print(f"Page Sequence: {self.page_sequence}")
        print(f"Number of Frames: {self.num_frames}")
        print(f"Total Page Accesses: {self.total_accesses}")
        print("=" * 60)
        
        # FIFO
        fifo_faults, fifo_rate = self.fifo()
        print(f"\nAlgorithm: FIFO (First-In-First-Out)")
        print(f"  Page Faults: {fifo_faults}")
        print(f"  Page Hits:   {self.total_accesses - fifo_faults}")
        print(f"  Fault Rate:  {fifo_rate:.2%}")
        
        # LRU
        lru_faults, lru_rate = self.lru()
        print(f"\nAlgorithm: LRU (Least Recently Used)")
        print(f"  Page Faults: {lru_faults}")
        print(f"  Page Hits:   {self.total_accesses - lru_faults}")
        print(f"  Fault Rate:  {lru_rate:.2%}")
        
        # OPT
        opt_faults, opt_rate = self.opt()
        print(f"\nAlgorithm: OPT (Optimal / MIN)")
        print(f"  Page Faults: {opt_faults}")
        print(f"  Page Hits:   {self.total_accesses - opt_faults}")
        print(f"  Fault Rate:  {opt_rate:.2%}")
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print(f"  FIFO: {fifo_faults} faults ({fifo_rate:.2%})")
        print(f"  LRU:  {lru_faults} faults ({lru_rate:.2%})")
        print(f"  OPT:  {opt_faults} faults ({opt_rate:.2%})")
        print("=" * 60)
        
        return {
            'fifo': {'faults': fifo_faults, 'rate': fifo_rate},
            'lru': {'faults': lru_faults, 'rate': lru_rate},
            'opt': {'faults': opt_faults, 'rate': opt_rate}
        }


def main():
    """Main function - run the paging simulator with the test sequence"""
    # Test with the given page sequence and 3 frames
    page_sequence = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    num_frames = 3
    
    simulator = PagingSimulator(num_frames, page_sequence)
    results = simulator.run_all()
    
    # Verify expected results
    # For this sequence with 3 frames:
    # FIFO typically: 9 faults (rate: 75%)
    # LRU typically: 10 faults (rate: 83.33%)
    # OPT typically: 7 faults (rate: 58.33%)
    print("\nVerification notes:")
    print(f"  FIFO faults should be 9: got {results['fifo']['faults']}")
    print(f"  LRU faults should be 10: got {results['lru']['faults']}")
    print(f"  OPT faults should be 7: got {results['opt']['faults']}")


if __name__ == "__main__":
    main()
