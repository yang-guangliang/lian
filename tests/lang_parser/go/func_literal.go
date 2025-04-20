1+func (c *Client)int{return 1}
func() string {
	func(nums ...int) int {
		241
	}(1,2,4,5)
}
func(a, b int, callback func(int, int) int) int {
	 callback(a, b)
}(10, 20, func(x, y int) int {
	 x * y
})