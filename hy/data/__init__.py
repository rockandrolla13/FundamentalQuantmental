"""The data module (reviews/2026_10_23_architecture_review.md; design: data module).

Every run reads its data through one `DataView` at one decision time. Vendor knowledge lives only in
`hy.data.adapters`. The record types (`records`) and the point-in-time rule (`pit`) are the stable core.
"""
