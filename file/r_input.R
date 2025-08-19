library(readxl)
library(dplyr)

data_1 <-read_excel("C:\\Users\\shiva\\Downloads\\data_R.XLSX")

data_1


# To sort in descending order 
arrange(data_1, desc("State/Union Territory"))