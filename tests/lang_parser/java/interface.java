import java.math.BigDecimal;

public interface BankAccount {

    int NUM_STUDENTS = 100;

    public enum Grayscale{DARK, Light};

    record R2() {
        public @interface ClassPreamble {
            String author();
            String date();
            int currentRevision() default 1;
        }
    }

    void deposit(BigDecimal amount);

    void withdraw(BigDecimal amount);

    BigDecimal getBalance();

    void transfer(BankAccount destinationAccount, BigDecimal amount);

    String getAccountHolderName();

    void setAccountHolderName(String accountHolderName);

    String getAccountNumber();

    void freezeAccount();

    void unfreezeAccount();

    boolean isAccountFrozen();

    void closeAccount();
}
