package main

import m"github.com/user/repo/package"
import (
    "fmt";m "math"
    _"net/http/pprof"
    . "./localpkg"
)

func run() {
	// create client
	config, err := client.LoadConfig("./config.json")
	if err != nil {
		fmt.Println("load config fail")
		return
	}

	// create wallet
	wallet, err := blockchain.LoadWallet(config.WalletCfg.PubKeyPath, config.WalletCfg.PriKeyPath)
	if err != nil {
		fmt.Println("Create wallet...")
		// load wallet fail
		wallet = blockchain.CreateWallet()
		// create new wallet
		err = wallet.SaveWallet(config.WalletCfg.PubKeyPath, config.WalletCfg.PriKeyPath)
		if err != nil {
			fmt.Println("Create wallet fail")
			return
		}
	}

	// initialize the chain
	chain, err := blockchain.LoadChain(config.ChainCfg.ChainDataBasePath, config.ChainCfg.LogPath)
	if err != nil {
		fmt.Println("Create chain fail")
		return
	}

	// create client
	c, err := client.CreateClient(config, chain, wallet)
	if err != nil {
		fmt.Println("Create client fail")
		return
	}

	// run client
	var wg sync.WaitGroup
	var exitChan = make(chan struct{})
	wg.Add(1)
	fmt.Println("Run client")
	go c.Run(&wg, exitChan)

	<-exitChan
	wg.Wait()
}

// MessageType represents the type of message received.
type MessageType uint8

// Constants representing different message types for handling.
const (
	BlockMsg       MessageType = iota // Message type for handling blocks
	TransactionMsg                    
	ConsensusMsg                      
)

// Message represents a generic message type transmitted over the P2P network.
type Message struct {
	Type MessageType
	Data []byte
}

// UnpackMessage decodes the binary data into a Message struct.
func UnpackMessage(rw *bufio.Reader) (*Message, error) {
	lenBuf := make([]byte, 8)
	_, err := io.ReadFull(rw, lenBuf)
	if err != nil {
		return nil, err
	}

	// Retrieve message length and read the message content
	msgLen := binary.BigEndian.Uint64(lenBuf)
	msgBuf := make([]byte, msgLen)
	_, err = io.ReadFull(rw, msgBuf)
	if err != nil {
		return nil, err
	}

	// Verify CRC32 checksum for data integrity
	checkBuf := make([]byte, 4)
	_, err = io.ReadFull(rw, checkBuf)
	if err != nil {
		return nil, err
	}
	readChecksum := binary.BigEndian.Uint32(checkBuf)

	dataBuf := bytes.NewBuffer(nil)
	dataBuf.Write(lenBuf)
	dataBuf.Write(msgBuf)
	calculatedChecksum := crc32.ChecksumIEEE(dataBuf.Bytes())
	if readChecksum != calculatedChecksum {
		return nil, errors.New("checksum verification failed")
	}

	// Unmarshal the message content into a Message struct
	var msg Message
	err = json.Unmarshal(msgBuf, &msg)
	return &msg, err
}

const (
	pi = 3.14
)

var (
	name string
	age  int
)

type Person struct {
	name string
	age  int
}

func newPerson(name string, age int) *Person {
	return &Person{name: name, age: age}
}

func (p *Person) greet() string {
	return "Hello, " + p.name
}

products = []struct {
    Name  string
    Price float64
}{
	{Name: "Tea", Price: 1.99},
	{Name: "Coffee", Price: 2.45},
}

new(struct{*int`fi`} | (~int | ~string), a + b)

func main() {
	x := 5
	y := 10
	z := x + y
	fmt.Println("Sum:", z)

	if z > 10 {
		fmt.Println("> 10")
	} else {
		fmt.Println("<= 10")
	}

	for i := 0; i < 5; i++ {
		fmt.Println("index:", i)
        if(i % 3 == 0) {
            continue
        }
        
	}

	switch x {
	case 1:
		fmt.Println("1")
	case 2:
		fmt.Println("Two")
        break
	default:
		fmt.Println("Other")
	}

	a := []int{1, 2, 3}
	for _, val := range a {
		fmt.Println("value:", val)
	}

	defer fmt.Println("End ")

	return
}
