class ConversionThread(QThread):
    progress = pyqtSignal(str, int, int)  # Signal to update progress: pdf name, current, total count
    gif_created = pyqtSignal(str, str)  # Signal to notify GIF creation: gif name, size

    def __init__(self, pdf_list, output_dir, fca_value, frame_value, opt_value, convert_path):
        super().__init__()
        self.pdf_list = pdf_list
        self.output_dir = output_dir
        self.fca_value = fca_value
        self.frame_value = frame_value
        self.opt_value = opt_value
        self.convert_path = convert_path  # Path to ImageMagick's convert executable

    def run(self):
        total_files = len(self.pdf_list)

        for idx, pdf_path in enumerate(self.pdf_list):
            pdf_name = os.path.basename(pdf_path)  # Get the PDF filename
            gif_name = pdf_name.replace('.pdf', '.gif')  # Create the GIF name
            pdf_dir = os.path.dirname(pdf_path)  # Get the directory of the current PDF
            gif_path = os.path.join(pdf_dir, gif_name)  # Save the GIF in the same directory as the PDF

            # Construct the FCA and Frame part of the command
            if self.fca_value == "Yes" and self.frame_value == "Loop":
                fca_frame_cmd = "300 -loop 0"
            elif self.fca_value == "No" and self.frame_value == "Loop":
                fca_frame_cmd = "300 -loop 0"

            elif self.fca_value == "Yes" and self.frame_value == "2":
                fca_frame_cmd = "300 -loop 1"
            elif self.fca_value == "No" and self.frame_value == "2":
                fca_frame_cmd = "-200 -loop 5"

            elif self.fca_value == "Yes" and self.frame_value == "3":
                fca_frame_cmd = "300 -loop 1"
            elif self.fca_value == "No" and self.frame_value == "3":
                fca_frame_cmd = "200 -loop 4"

            elif self.fca_value == "Yes" and self.frame_value == "4":
                fca_frame_cmd = "300 -loop 1"
            elif self.fca_value == "No" and self.frame_value == "4":
                fca_frame_cmd = "200 -loop 3"

            elif self.fca_value == "Yes" and self.frame_value == "5":
                fca_frame_cmd = "250 -loop 1"
            elif self.fca_value == "No" and self.frame_value == "5":
                fca_frame_cmd = "166 -loop 3"

            elif self.fca_value == "Yes" and self.frame_value == "6":
                fca_frame_cmd = "250 -loop 1"
            elif self.fca_value == "No" and self.frame_value == "6":
                fca_frame_cmd = "150 -loop 3"

            elif self.fca_value == "Yes" and self.frame_value == "7":
                fca_frame_cmd = "200 -loop 1"
            elif self.fca_value == "No" and self.frame_value == "7":
                fca_frame_cmd = "140 -loop 3"

            elif self.fca_value == "Yes" and self.frame_value == "8":
                fca_frame_cmd = "200 -loop 1"
            elif self.fca_value == "No" and self.frame_value == "8":
                fca_frame_cmd = "166 -loop 2"

            elif self.fca_value == "Yes" and self.frame_value == "9":
                fca_frame_cmd = "200 -loop 1"
            elif self.fca_value == "No" and self.frame_value == "9":
                fca_frame_cmd = "150 -loop 2"

            # Add conditions for Frame 3 here if needed.
            else:
                fca_frame_cmd = "-delay 500 -loop 0"  # Default command if no match
            # Construct the Optimization part of the command
            opt_cmd = "-layers Optimize" if self.opt_value == "Yes" else ""
            opt_cmd1 = "-coalesce -dispose background -alpha background +dither"
            opt_cmd2 = "+map -scale 25% +set comment"

            # Final ImageMagick convert command
            cmd = [self.convert_path, '-density', '288', '-delay']
            cmd += fca_frame_cmd.split()
            cmd += opt_cmd1.split()

            if opt_cmd:
                cmd += opt_cmd.split()

            cmd += opt_cmd2.split()
            cmd += [pdf_path, gif_path]

            # Execute the command
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                print(f"Command executed successfully: {cmd}")
            except subprocess.CalledProcessError as e:
                print(f"Error occurred while executing command: {e.stderr.decode()}")
                continue

            # Calculate the exact size of the created GIF
            try:
                gif_size_bytes = self.get_exact_file_size(gif_path)
                gif_size_kb = gif_size_bytes / 1024
                size_info = f"{gif_size_bytes} Bytes ({gif_size_kb:.2f} KB)"
                self.gif_created.emit(gif_path, size_info)
            except Exception as e:
                print(f"Error calculating size for {gif_path}: {e}")
                continue

            # Emit progress update
            self.progress.emit(pdf_name, idx + 1, total_files)

    @staticmethod
    def get_exact_file_size(file_path):
        """
        Get the exact size of a file in bytes using 'du' or fallback to os.stat.
        """
        try:
            result = subprocess.run(['du', '-b', file_path], capture_output=True, text=True, check=True)
            size = int(result.stdout.split()[0])  # Get the size in bytes
            return size
        except Exception as e:
            print(f"'du' command failed, falling back to os.stat: {e}")
            stat = os.stat(file_path)
            return stat.st_size
